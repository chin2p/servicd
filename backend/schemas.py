from pydantic import BaseModel


class ExtractedPart(BaseModel):
    name: str
    brand: str | None = None
    price_dollars: float | None = None #dollars, as priced on receipt

class ReceiptExtraction(BaseModel):
    maintenance_type: str | None = None
    miles_at_service: int | None = None
    date: str | None = None   # "YYYY-MM-DD"
    parts: list[ExtractedPart] = []
    