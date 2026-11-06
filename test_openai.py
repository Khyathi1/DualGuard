
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OpenAI API key not found. Check your .env file.")

client = OpenAI(api_key=api_key)

response = client.responses.create(
    model="gpt-5.4",
    input="Explain prompt injection in one sentence."
)

print(response.output_text)
