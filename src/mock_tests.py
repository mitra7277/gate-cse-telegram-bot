import random
import time
from typing import List, Dict

# Assuming 1 mark for each for simplicity in this implementation
# But keeping structure extensible
def generate_mock_test(all_questions: List[Dict], num_questions: int = 5) -> List[Dict]:
    """Generates a mock test with a mix of questions."""
    if len(all_questions) < num_questions:
        num_questions = len(all_questions)
    return random.sample(all_questions, num_questions)

def calculate_mock_score(responses: List[Dict]) -> Dict:
    """
    Calculates score based on responses.
    responses format: [{'question': q_dict, 'user_answers': [...], 'is_correct': bool, 'score': float}]
    """
    total_score = 0.0
    correct_count = 0
    incorrect_count = 0

    for resp in responses:
        total_score += resp['score']
        if resp['is_correct']:
            correct_count += 1
        else:
            incorrect_count += 1

    return {
        "total_score": round(total_score, 2),
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "total_questions": len(responses)
    }

def format_mock_report(score_data: Dict) -> str:
    """Formats the final score report."""
    return (
        "📊 *Mock Test Report*\n\n"
        f"Total Questions: {score_data['total_questions']}\n"
        f"✅ Correct: {score_data['correct_count']}\n"
        f"❌ Incorrect: {score_data['incorrect_count']}\n"
        f"🏆 *Final Score: {score_data['total_score']}*"
    )
