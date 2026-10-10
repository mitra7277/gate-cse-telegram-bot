import pytest
from src.mock_tests import calculate_mock_score, generate_mock_test

def test_generate_mock_test():
    questions = [{"id": i} for i in range(10)]
    mock = generate_mock_test(questions, num_questions=3)
    assert len(mock) == 3

    # Test taking more than available
    mock_all = generate_mock_test(questions, num_questions=15)
    assert len(mock_all) == 10

def test_calculate_mock_score():
    responses = [
        {"is_correct": True, "score": 1.0},
        {"is_correct": False, "score": -0.33},
        {"is_correct": True, "score": 2.0},
        {"is_correct": False, "score": 0.0} # Incorrect MSQ
    ]

    result = calculate_mock_score(responses)

    assert result["total_questions"] == 4
    assert result["correct_count"] == 2
    assert result["incorrect_count"] == 2

    # 1.0 - 0.33 + 2.0 + 0.0 = 2.67
    assert result["total_score"] == 2.67
