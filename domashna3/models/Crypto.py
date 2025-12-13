from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Crypto(Base):
    __tablename__ = "coins"
    id = Column(String, primary_key=True)
    symbol = Column(String)
    name = Column(String)
    market_cap = Column(Float)
    market_cap_rank = Column(Float)
