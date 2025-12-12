from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, String, Float, func
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List
from pydantic import BaseModel
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../domashna1/crypto.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class Crypto(Base):
    __tablename__ = "coins"
    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    market_cap = Column(Float)
    market_cap_rank = Column(Float)

# ⚙️ 4. Pydantic schema
class CryptoSchema(BaseModel):
    id: str
    symbol: str
    name: str
    market_cap: float | None = None
    market_cap_rank: float | None = None

    class Config:
        from_attributes = True

app = FastAPI(title="Crypto API Test")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/cryptos", response_model=List[CryptoSchema])
def read_cryptos(db: Session = Depends(get_db)):
    return db.query(Crypto).all()

@app.get("/selected_crypto/id/{crypto_id}", response_model=CryptoSchema)
def get_crypto_by_id(crypto_id: str, db: Session = Depends(get_db)):
    crypto = db.query(Crypto).filter(Crypto.id == crypto_id).first()
    if not crypto:
        raise HTTPException(status_code=404, detail="Crypto not found")
    return crypto

@app.get("/selected_crypto", response_model=CryptoSchema)
def get_crypto_by_symbol(symbol: str, db: Session = Depends(get_db)):
    crypto = db.query(Crypto).filter(func.lower(Crypto.symbol) == symbol.lower()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail="Crypto not found")
    return crypto
