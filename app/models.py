from sqlalchemy import Column, Integer, String
from .database import Base


metadata = Base.metadata

class ScapedData(Base):
    __tablename__ = 'scraped-data'

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    text = Column(String(45), nullable=False)

