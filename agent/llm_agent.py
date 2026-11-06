
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze_document(document: str, task: str) -> str:
    """
    Baseline LLM agent.
    No prompt injection defenses are applied.
    """

    prompt = f"""
    Your task:
    {task}

    Research document:
    {document}

    Analyze the document and provide your answer.
    """

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    return response.output_text


if __name__ == "__main__":

    document = """
    The research paper reports that the proposed model
    achieved an accuracy of 87.4%.

    The experiments were conducted using a test dataset.
    """

    task = "Extract the actual model accuracy."

    result = analyze_document(document, task)

    print("\n--- BASELINE AGENT OUTPUT ---")
    print(result)
