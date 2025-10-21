# study_guide_generator.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise Exception("❌ Missing OPENAI_API_KEY in .env")

# Initialize new OpenAI client (supports sk-proj-... keys)
client = OpenAI(api_key=OPENAI_API_KEY)

# === Flashcard Generator ===
def get_flashcard_chain():
    def run(input_text: str):
        prompt = f"""
        Convert the following study notes into concise flashcards.
        Each flashcard should follow this format:

        Q: [Question]
        A: [Answer]

        Notes:
        {input_text}
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    return type("FlashcardChain", (), {"run": staticmethod(run)})

# === Quiz Generator ===
def get_quiz_chain():
    def run(input_text: str):
        prompt = f"""
        Generate 5 multiple-choice questions based on the following notes.
        Each question should have 4 options (A, B, C, D) and mark the correct answer with (*).

        Notes:
        {input_text}
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    return type("QuizChain", (), {"run": staticmethod(run)})
