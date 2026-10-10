import pytest
from unittest.mock import patch, MagicMock
from src.ai_generation import generate_ai_question
import json

@pytest.fixture
def mock_gemini_client():
    with patch("src.ai_generation.client") as mock_client:
        yield mock_client

def test_generate_ai_question_success(mock_gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "id": "ai_123",
        "topic": "OS",
        "type": "MCQ",
        "question": "What is OS?",
        "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
        "correct_answers": ["A"],
        "explanation": "Because.",
        "source": "AI-Generated",
        "difficulty": "Easy"
    })
    mock_gemini_client.models.generate_content.return_value = mock_response

    with patch("src.ai_generation.GEMINI_API_KEY", "dummy_key"):
        result = generate_ai_question("OS")
        assert result is not None
        assert result["topic"] == "OS"
        assert result["difficulty"] == "Easy"
        assert result["source"] == "AI-Generated"
        mock_gemini_client.models.generate_content.assert_called_once()

def test_generate_ai_question_missing_fields(mock_gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "topic": "OS",
        # Missing question, options, correct_answers, etc.
    })
    mock_gemini_client.models.generate_content.return_value = mock_response

    with patch("src.ai_generation.GEMINI_API_KEY", "dummy_key"):
        result = generate_ai_question("OS")
        assert result is None

def test_generate_ai_question_invalid_answers(mock_gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "id": "ai_123",
        "topic": "OS",
        "type": "MCQ",
        "question": "What is OS?",
        "options": {"A": "A"},
        "correct_answers": ["B"], # B is not in options
        "explanation": "Because.",
        "source": "AI-Generated",
        "difficulty": "Easy"
    })
    mock_gemini_client.models.generate_content.return_value = mock_response

    with patch("src.ai_generation.GEMINI_API_KEY", "dummy_key"):
        result = generate_ai_question("OS")
        assert result is None

def test_generate_ai_question_api_failure(mock_gemini_client):
    mock_gemini_client.models.generate_content.side_effect = Exception("API Error")

    with patch("src.ai_generation.GEMINI_API_KEY", "dummy_key"):
        result = generate_ai_question("OS")
        assert result is None

def test_generate_ai_question_with_history(mock_gemini_client):
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "id": "ai_123",
        "topic": "OS",
        "type": "MCQ",
        "question": "What is OS?",
        "options": {"A": "A"},
        "correct_answers": ["A"],
        "explanation": "Because.",
        "source": "AI-Generated",
        "difficulty": "Easy"
    })
    mock_gemini_client.models.generate_content.return_value = mock_response

    history = [{"question": "What is a process?"}]
    with patch("src.ai_generation.GEMINI_API_KEY", "dummy_key"):
        result = generate_ai_question("OS", history=history)
        assert result is not None
        call_args = mock_gemini_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]
        assert "What is a process?" in prompt
