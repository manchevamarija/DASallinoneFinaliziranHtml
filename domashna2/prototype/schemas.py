from pydantic import BaseModel

class CryptoSchema(BaseModel):
    id: int
    symbol: str
    name: str
    market_cap: float
    market_cap_rank: int

    class Config:
        from_attributes = True  # For FastAPI v2
