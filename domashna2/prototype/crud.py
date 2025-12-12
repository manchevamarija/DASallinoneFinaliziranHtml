from sqlalchemy.orm import Session
from models import CryptoPrice
from datetime import date

def get_prices_by_symbol(db: Session, symbol: str, start: date, end: date):
    return db.query(CryptoPrice)\
             .filter(CryptoPrice.symbol == symbol)\
             .filter(CryptoPrice.date >= start)\
             .filter(CryptoPrice.date <= end)\
             .order_by(CryptoPrice.date.asc())\
             .all()
