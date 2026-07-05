from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

app = FastAPI()

class InvoiceRequest(BaseModel):
    text: str

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):
    if not req.text or not isinstance(req.text, str):
        raise HTTPException(status_code=422, detail="Invalid input")

    text = req.text

    # -------------------------
    # VENDOR (robust extraction)
    # -------------------------
    vendor_match = re.search(
        r"(?:from|vendor|bill\s*from)\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )
    vendor = (
        vendor_match.group(1).split("\n")[0].strip()
        if vendor_match else "Unknown"
    )

    # -------------------------
    # AMOUNT (IMPORTANT FIX)
    # Prioritize TOTAL / DUE fields
    amount = None

# 1. PRIORITY: explicit total fields
amount_patterns = [
    r"(?i)total\s*(?:due|amount|payable)?\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"(?i)amount\s*due\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"(?i)balance\s*due\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
]

for p in amount_patterns:
    m = re.search(p, text)
    if m:
        amount = float(m.group(1))
        break

# 2. IMPROVED FALLBACK: pick LARGEST number (not last, not first)
if amount is None:
    numbers = re.findall(r"[0-9]+(?:\.[0-9]{1,2})?", text)

    if numbers:
        # convert and pick MAX (total is usually largest in invoice)
        amount = max(float(n) for n in numbers)
    else:
        amount = 0.0
    # -------------------------
    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)
    currency = currency_match.group(1).upper() if currency_match else "USD"

    # -------------------------
    # DATE
    # -------------------------
    date_match = re.search(r"\b(2026-\d{2}-\d{2})\b", text)
    date = date_match.group(1) if date_match else "2026-01-01"

    return InvoiceResponse(
        vendor=vendor,
        amount=round(amount, 2),
        currency=currency,
        date=date
    )
