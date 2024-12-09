from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    stats = Column(JSON)  # e.g., {"wins": 10, "losses": 5}
    unlocked_cards = Column(JSON)  # List of card IDs

engine = create_engine("sqlite:///game.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
