import json
import google.generativeai as genai
from src.config import GEMINI_API_KEY
from src.logger import get_logger

logger = get_logger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_ai_question(topic: str) -> dict:
    """
    Generates a new GATE CSE style question using Gemini API.
    Returns a dictionary matching the structure of questions.json.
    """
    if not GEMINI_API_KEY:
        logger.warning("Gemini API key not set. Cannot generate AI questions.")
        return None

    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
    Generate a challenging, original GATE CSE style question for the topic: {topic}.
    It can be either an MCQ (1 correct answer) or an MSQ (multiple correct answers).
    Ensure the question is mathematically and conceptually sound.

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
        "source": "AI-Generated"
    }}
    Do not include markdown formatting like ```json in the output, just the raw JSON object.
    """

    import re
    try:
        response = model.generate_content(prompt)
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
        assert "question" in question_data
        assert "options" in question_data
        assert "correct_answers" in question_data
        assert question_data["source"] == "AI-Generated"

        return question_data

    except Exception as e:
        logger.error(f"Failed to generate or parse AI question: {e}")
        return None
