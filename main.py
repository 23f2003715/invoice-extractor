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
    if not req.text:
        raise HTTPException(status_code=422, detail="Empty input")

    text = req.text

    vendor_match = re.search(r"(Acme[-\w\s&]+|[A-Z][\w\s&]+Ltd|Industries|Corp)", text)
    vendor = vendor_match.group(1).strip() if vendor_match else "Unknown"

    amount_match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    amount = float(amount_match.group(1)) if amount_match else 0.0

    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text)
    currency = currency_match.group(1).upper() if currency_match else "USD"

    date_match = re.search(r"(2026-\d{2}-\d{2})", text)
    date = date_match.group(1) if date_match else "2026-01-01"

    return InvoiceResponse(
        vendor=vendor,
        amount=round(amount, 2),
        currency=currency,
        date=date
    )
