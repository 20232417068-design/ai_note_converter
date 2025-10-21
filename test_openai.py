from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello from AI Note Converter!"}]
    )
    print("✅ API key works! Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print("❌ API key test failed:", e)
