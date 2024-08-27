import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from .env file
load_dotenv()

# Configure the service with your API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_and_save_story():
    """
    Generates a 500-word story using Gemini Pro and extracts token usage metadata.

    Returns:
        tuple: A tuple containing the generated story and the usage metadata.
    """

    prompt = "Tell me a 500-word story about a brave knight and a magical dragon."

    # Instantiate the GenerativeModel
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Generate text using the specified model and prompt, with generation config
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,  # Only one candidate for now
            max_output_tokens=512,  # Adjust for desired story length
            temperature=0.5,
        ),
    )

    # Extract the generated text and usage metadata
    story = response.text
    usage_metadata = response.usage_metadata

    return story, usage_metadata


if __name__ == "__main__":
    story, usage_metadata = generate_and_save_story()

    print("Generated Story:")
    print(story)

    print("\nUsage Metadata:")
    print("Input Tokens:", usage_metadata.prompt_token_count)
    print("Output Tokens:", usage_metadata.candidates_token_count)
    print("Total Tokens:", usage_metadata.total_token_count)
