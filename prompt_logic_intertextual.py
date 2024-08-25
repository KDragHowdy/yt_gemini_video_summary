import json
from models import get_gemini_flash_model_json
import time


def analyze_intertextual_references(
    video_analysis, transcript_analysis, chunk_start, chunk_end
):
    max_retries = 3
    retry_delay = 1  # Start with 1 second delay

    for attempt in range(max_retries):
        try:
            prompt = f"""
            Analyze the following video content description and transcript for intertextual references:

            Video Content Description:
            {video_analysis}

            Transcript:
            {transcript_analysis}

            Identify and explain any references to literary works, philosophical concepts, historical events, scientific theories, pop culture, AI technology, research papers, internet culture, or other notable ideas.

            Format the output as a JSON array of objects with the following structure:
            [
                {{
                    "type": "literary/philosophical/historical/scientific/pop_culture/ai_tech/research/internet_culture/other",
                    "reference": "The actual reference",
                    "context": "How it was used in the video",
                    "explanation": "Brief explanation of the reference",
                    "significance": "Why it's important in this context"
                }}
            ]

            Ensure that the output is a valid JSON array. Do not include any text before or after the JSON array.
            """

            model = get_gemini_flash_model_json()
            response = model.generate_content(prompt)
            intertextual_analysis = response.text

            print(
                f"Debug: Raw intertextual analysis content for chunk {chunk_start}-{chunk_end}:\n{intertextual_analysis[:500]}..."
            )

            # Attempt to parse the JSON
            parsed_analysis = json.loads(intertextual_analysis)

            # Ensure the parsed result is a list
            if not isinstance(parsed_analysis, list):
                raise ValueError("Parsed JSON is not a list")

            return json.dumps({"references": parsed_analysis}, indent=2)

        except (json.JSONDecodeError, ValueError) as e:
            print(
                f"Debug: JSON parsing error for chunk {chunk_start}-{chunk_end}: {str(e)}"
            )
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Debug: Falling back to a default structure.")
                return json.dumps({"references": []}, indent=2)


# ... (rest of the file remains unchanged)
