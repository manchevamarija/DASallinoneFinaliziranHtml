from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Crypto(Base):
    __tablename__ = "cryptos"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    market_cap = Column(Float)
    market_cap_rank = Column(Integer)
<<<<<<< HEAD
=======


>>>>>>> 1d0ece7728e87059046f025d99f499098ed004d0
