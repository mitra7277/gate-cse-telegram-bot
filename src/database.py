import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    current_streak = Column(Integer, default=0)
    highest_streak = Column(Integer, default=0)

    attempts = relationship("Attempt", back_populates="user")
    incorrect_answers = relationship("IncorrectAnswer", back_populates="user")
    mock_tests = relationship("MockTestAttempt", back_populates="user")

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(String, index=True) # Assuming string IDs for questions
    topic = Column(String, index=True)
    is_correct = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="attempts")

class IncorrectAnswer(Base):
    __tablename__ = "incorrect_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(String, index=True)
    topic = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    needs_revision = Column(Boolean, default=True)

    user = relationship("User", back_populates="incorrect_answers")

class MockTestAttempt(Base):
    __tablename__ = "mock_test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float)
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    incorrect_answers_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON) # Store question IDs and responses for review

    user = relationship("User", back_populates="mock_tests")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
