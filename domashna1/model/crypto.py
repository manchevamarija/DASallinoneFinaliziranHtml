from sqlalchemy import Column, Integer, String, Float
from domashna1.data.crypto_db import Base

class Crypto(Base):
    __tablename__ = "cryptos"  # Make sure this matches your table name in crypto.db

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    market_cap = Column(Float)
    market_cap_rank = Column(Integer)
