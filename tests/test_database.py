import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, User, Attempt, IncorrectAnswer

# Use in-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_create_user(db_session):
    user = User(telegram_id=12345, username="testuser", first_name="Test")
    db_session.add(user)
    db_session.commit()

    fetched_user = db_session.query(User).filter_by(telegram_id=12345).first()
    assert fetched_user is not None
    assert fetched_user.username == "testuser"
    assert fetched_user.current_streak == 0

def test_record_attempt(db_session):
    user = User(telegram_id=12345)
    db_session.add(user)
    db_session.commit()

    attempt = Attempt(user_id=user.id, question_id="q1", topic="OS", is_correct=True)
    db_session.add(attempt)
    db_session.commit()

    fetched_attempt = db_session.query(Attempt).filter_by(user_id=user.id).first()
    assert fetched_attempt is not None
    assert fetched_attempt.topic == "OS"
    assert fetched_attempt.is_correct is True

def test_incorrect_answer_logging(db_session):
    user = User(telegram_id=12345)
    db_session.add(user)
    db_session.commit()

    inc = IncorrectAnswer(user_id=user.id, question_id="q2", topic="DBMS")
    db_session.add(inc)
    db_session.commit()

    fetched_inc = db_session.query(IncorrectAnswer).filter_by(user_id=user.id).first()
    assert fetched_inc.needs_revision is True
    assert fetched_inc.topic == "DBMS"
