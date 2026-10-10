import pytest
from unittest.mock import AsyncMock, MagicMock
from src.handlers import start_topic_practice, handle_answer

# Mock the loaded QUESTIONS list locally in the test scope
mocked_questions = [
    {"id": "q1", "topic": "OS", "type": "MCQ", "question": "Q1", "options": {"A": "1"}, "correct_answers": ["A"], "explanation": "E1", "source": "S1"},
    {"id": "q2", "topic": "OS", "type": "MCQ", "question": "Q2", "options": {"A": "1"}, "correct_answers": ["A"], "explanation": "E2", "source": "S2"},
    {"id": "q3", "topic": "OS", "type": "MCQ", "question": "Q3", "options": {"A": "1"}, "correct_answers": ["A"], "explanation": "E3", "source": "S3"},
    {"id": "q4", "topic": "DBMS", "type": "MCQ", "question": "Q4", "options": {"A": "1"}, "correct_answers": ["A"], "explanation": "E4", "source": "S4"}
]

@pytest.fixture
def mock_update_context():
    update = MagicMock()
    update.callback_query = AsyncMock()
    update.callback_query.data = ""
    update.callback_query.message = AsyncMock()
    update.effective_user = MagicMock()

    context = MagicMock()
    context.user_data = {}
    return update, context

@pytest.mark.asyncio
async def test_start_topic_practice_cycle(monkeypatch, mock_update_context):
    update, context = mock_update_context
    update.callback_query.data = "topic_OS"

    # Patch QUESTIONS in handlers to use our mock
    import src.handlers
    monkeypatch.setattr(src.handlers, "QUESTIONS", mocked_questions)

    # Mock send_question so we don't actually try to send telegram messages
    mock_send = AsyncMock()
    monkeypatch.setattr(src.handlers, "send_question", mock_send)

    # Call multiple times to exhaust the cycle and reset
    asked_ids = []

    for _ in range(4):
        await start_topic_practice(update, context)
        current_q = mock_send.call_args[0][2]
        asked_ids.append(current_q['id'])

    # The first 3 should be unique (q1, q2, q3)
    assert len(set(asked_ids[:3])) == 3
    assert set(asked_ids[:3]) == {"q1", "q2", "q3"}

    # The 4th should be a reset, so it's a valid OS question
    # and shouldn't be the same as the 3rd one
    assert asked_ids[3] in ["q1", "q2", "q3"]
    assert asked_ids[3] != asked_ids[2]

@pytest.mark.asyncio
async def test_start_topic_practice_independent_users(monkeypatch):
    # Setup for User 1
    update1 = MagicMock()
    update1.callback_query = AsyncMock()
    update1.callback_query.data = "topic_OS"
    context1 = MagicMock()
    context1.user_data = {}

    # Setup for User 2
    update2 = MagicMock()
    update2.callback_query = AsyncMock()
    update2.callback_query.data = "topic_OS"
    context2 = MagicMock()
    context2.user_data = {}

    import src.handlers
    monkeypatch.setattr(src.handlers, "QUESTIONS", mocked_questions)

    mock_send = AsyncMock()
    monkeypatch.setattr(src.handlers, "send_question", mock_send)

    # User 1 asks 3 questions
    for _ in range(3):
        await start_topic_practice(update1, context1)

    # User 2 asks 1 question
    await start_topic_practice(update2, context2)

    # Ensure their contexts track asked questions separately
    assert len(context1.user_data['asked_questions']['OS']) == 3
    assert len(context2.user_data['asked_questions']['OS']) == 1

@pytest.mark.asyncio
async def test_single_question_topic(monkeypatch, mock_update_context):
    update, context = mock_update_context
    update.callback_query.data = "topic_DBMS" # Only q4 is DBMS

    import src.handlers
    monkeypatch.setattr(src.handlers, "QUESTIONS", mocked_questions)

    mock_send = AsyncMock()
    monkeypatch.setattr(src.handlers, "send_question", mock_send)

    await start_topic_practice(update, context)

    assert context.user_data.get('single_question_topic') is True
