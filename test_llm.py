import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

resp = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="In 2 lines, what is an 8D report in manufacturing quality?",
)
print(resp.text)