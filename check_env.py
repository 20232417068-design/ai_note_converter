import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
print("Loaded key prefix:", key[:20] if key else "No key loaded!")
