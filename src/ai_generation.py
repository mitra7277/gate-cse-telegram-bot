import json
import re
from google import genai
from src.config import GEMINI_API_KEY
from src.logger import get_logger

logger = get_logger(__name__)

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

def generate_ai_question(topic: str, history: list = None) -> dict:
    """
    Generates a new GATE CSE style question using Gemini API.
    Returns a dictionary matching the structure of questions.json.
    """
    if not GEMINI_API_KEY or not client:
        logger.warning("Gemini API key not set. Cannot generate AI questions.")
        return None

    model = 'gemini-2.5-flash'

    history_str = ""
    if history:
        history_str = "Avoid generating questions similar to these concepts:\n"
        for i, q in enumerate(history[-5:]): # Limit to last 5 to save tokens
            history_str += f"- {q.get('question', '')[:100]}...\n"

    prompt = f"""
    Generate a challenging, original GATE CSE style question for the topic: {topic}.
    It can be either an MCQ (1 correct answer) or an MSQ (multiple correct answers).
    Ensure the question is mathematically and conceptually sound.

    {history_str}

    Return ONLY a valid JSON object with exactly this structure:
    {{
        "id": "ai_generated_xyz",
        "topic": "{topic}",
        "type": "MCQ" (or "MSQ"),
        "question": "The question text",
        "options": {{
            "A": "Option A text",
            "B": "Option B text",
            "C": "Option C text",
            "D": "Option D text"
        }},
        "correct_answers": ["A"] (or ["A", "C"] for MSQ),
        "explanation": "Detailed explanation of why the correct options are correct and others are wrong.",
        "source": "AI-Generated",
        "difficulty": "Easy" (or "Medium", "Hard")
    }}
    Do not include markdown formatting like ```json in the output, just the raw JSON object.
    """

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        # Attempt to parse the response as JSON
        text_response = response.text.strip()

        # Use regex to extract the JSON block if it's wrapped in markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text_response, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Fallback to the raw response if no markdown block is found
            json_str = text_response

        question_data = json.loads(json_str.strip())

        # Basic validation
        assert "question" in question_data, "Missing 'question' field"
        assert "options" in question_data, "Missing 'options' field"
        assert "correct_answers" in question_data, "Missing 'correct_answers' field"
        assert "explanation" in question_data, "Missing 'explanation' field"
        assert "topic" in question_data, "Missing 'topic' field"
        assert "difficulty" in question_data, "Missing 'difficulty' field"
        assert question_data.get("source") == "AI-Generated", "Source must be AI-Generated"

        # Verify correct_answers are valid keys in options
        for ans in question_data["correct_answers"]:
            assert ans in question_data["options"], f"Correct answer '{ans}' not found in options"

        return question_data

    except Exception as e:
        logger.error(f"Failed to generate or parse AI question: {e}")
        return None
