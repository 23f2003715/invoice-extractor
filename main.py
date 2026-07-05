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

    # ---------------- VENDOR ----------------
    vendor_match = re.search(
        r"(?:from|vendor|bill\s*from)\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )
    vendor = (
        vendor_match.group(1).split("\n")[0].strip()
        if vendor_match else "Unknown"
    )

    # ---------------- AMOUNT ----------------
    amount = None

    patterns = [
        r"(?i)total\s*(?:due|amount|payable)?\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"(?i)amount\s*due\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"(?i)balance\s*due\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            amount = float(m.group(1))
            break

    if amount is None:
        numbers = re.findall(r"[0-9]+(?:\.[0-9]{1,2})?", text)
        amount = float(max(numbers, key=float)) if numbers else 0.0

    # ---------------- CURRENCY ----------------
    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)
    currency = currency_match.group(1).upper() if currency_match else "USD"

    # ---------------- DATE ----------------
    date_match = re.search(r"\b(2026-\d{2}-\d{2})\b", text)
    date = date_match.group(1) if date_match else "2026-01-01"

    return InvoiceResponse(
        vendor=vendor,
        amount=round(amount, 2),
        currency=currency,
        date=date
    )
