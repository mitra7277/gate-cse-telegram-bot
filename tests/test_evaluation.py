import pytest
from src.evaluation import evaluate_mcq, evaluate_msq, evaluate_question

def test_evaluate_mcq_correct():
    is_correct, score = evaluate_mcq(["A"], ["A"], marks=1.0)
    assert is_correct is True
    assert score == 1.0

def test_evaluate_mcq_incorrect_negative_marking():
    is_correct, score = evaluate_mcq(["B"], ["A"], marks=1.0)
    assert is_correct is False
    assert score == -0.33

    is_correct, score = evaluate_mcq(["B"], ["A"], marks=2.0)
    assert is_correct is False
    assert score == -0.67

def test_evaluate_msq_correct_exact_match():
    is_correct, score = evaluate_msq(["A", "C"], ["A", "C"], marks=2.0)
    assert is_correct is True
    assert score == 2.0

    # Order shouldn't matter
    is_correct, score = evaluate_msq(["C", "A"], ["A", "C"], marks=2.0)
    assert is_correct is True
    assert score == 2.0

def test_evaluate_msq_incorrect_partial_match():
    is_correct, score = evaluate_msq(["A"], ["A", "C"], marks=2.0)
    assert is_correct is False
    assert score == 0.0

def test_evaluate_msq_incorrect_extra_match():
    is_correct, score = evaluate_msq(["A", "B", "C"], ["A", "C"], marks=2.0)
    assert is_correct is False
    assert score == 0.0

def test_evaluate_question_dispatch():
    is_correct, score = evaluate_question("MCQ", ["A"], ["A"])
    assert is_correct is True

    is_correct, score = evaluate_question("MSQ", ["A"], ["A", "B"])
    assert is_correct is False

def test_evaluate_invalid_type():
    with pytest.raises(ValueError):
        evaluate_question("NAT", ["10.5"], ["10.5"])
