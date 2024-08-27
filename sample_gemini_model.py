# sample_gemini_model.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def generate_and_save_story():
    """
    Generates a 500-word story using Gemini Pro and extracts token usage metadata.

    Returns:
        tuple: A tuple containing the generated story and the usage metadata.
    """

    response = genai.GenerativeModel(
        "gemini-1.5-flash",
        prompt="Tell me a 500-word story about a brave knight and a magical dragon.",
        generation_config={
            "temperature": 0.5,
            "top_p": 0.9,
            "top_k": 40,
        },
    )

    story = response.result
    usage_metadata = response.result.usage_metadata

    return story, usage_metadata


if __name__ == "__main__":
    story, usage_metadata = generate_and_save_story()

    print("Generated Story:")
    print(story)

    print("\nUsage Metadata:")
    print("Input Tokens:", usage_metadata.prompt_token_count)
    print("Output Tokens:", usage_metadata.candidates_token_count)
    print("Total Tokens:", usage_metadata.total_token_count)
