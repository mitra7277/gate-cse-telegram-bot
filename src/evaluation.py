from typing import List, Tuple

# GATE marking schemes generally:
# 1-mark MCQ: Correct +1, Incorrect -0.33
# 2-mark MCQ: Correct +2, Incorrect -0.66
# 1-mark MSQ/NAT: Correct +1, Incorrect 0
# 2-mark MSQ/NAT: Correct +2, Incorrect 0

def evaluate_mcq(user_answers: List[str], correct_answers: List[str], marks: float = 1.0) -> Tuple[bool, float]:
    """
    Evaluates an MCQ question.
    Only takes the first answer if multiple are somehow passed.
    Returns (is_correct, score)
    """
    if not user_answers or not correct_answers:
        return False, 0.0

    # MCQ should have exactly one correct answer
    correct_ans = correct_answers[0]
    user_ans = user_answers[0]

    if user_ans == correct_ans:
        return True, marks
    else:
        # Calculate negative marking (1/3rd of the marks)
        negative_marks = round((1/3) * marks, 2)
        return False, -negative_marks

def evaluate_msq(user_answers: List[str], correct_answers: List[str], marks: float = 1.0) -> Tuple[bool, float]:
    """
    Evaluates an MSQ question.
    Requires exact-set match. No negative marking for MSQs.
    Returns (is_correct, score)
    """
    if not user_answers or not correct_answers:
        return False, 0.0

    user_set = set(user_answers)
    correct_set = set(correct_answers)

    if user_set == correct_set:
        return True, marks
    else:
        return False, 0.0

def evaluate_question(q_type: str, user_answers: List[str], correct_answers: List[str], marks: float = 1.0) -> Tuple[bool, float]:
    """
    Dispatches to the correct evaluation function based on question type.
    """
    if q_type.upper() == 'MCQ':
        return evaluate_mcq(user_answers, correct_answers, marks)
    elif q_type.upper() == 'MSQ':
        return evaluate_msq(user_answers, correct_answers, marks)
    else:
        raise ValueError(f"Unknown question type: {q_type}")
