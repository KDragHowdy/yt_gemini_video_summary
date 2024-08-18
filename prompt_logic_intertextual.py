import google.generativeai as genai
import json
from datetime import datetime

model = genai.GenerativeModel(
    "gemini-1.5-flash", generation_config={"response_mime_type": "application/json"}
)


def analyze_intertextual_references(
    video_analysis, transcript_analysis, chunk_start, chunk_end
):
    prompt = f"""
    Analyze the following video content description and transcript for intertextual references:

    Video Content Description:
    {video_analysis}

    Transcript:
    {transcript_analysis}

    Identify and explain any references to literary works, philosophical concepts, historical events, scientific theories, pop culture, AI technology, research papers, internet culture, or other notable ideas.

    Using this JSON schema:
    Reference = {{
        "type": str,
        "reference": str,
        "context": str,
        "explanation": str,
        "significance": str
    }}

    Return a `list[Reference]`
    """

    response = model.generate_content(prompt)
    intertextual_analysis = response.text

    print(
        f"Debug: Raw intertextual analysis content for chunk {chunk_start}-{chunk_end}:\n{intertextual_analysis[:500]}..."
    )

    try:
        parsed_analysis = json.loads(intertextual_analysis)
        if not isinstance(parsed_analysis, list):
            raise ValueError("Parsed JSON is not a list")
    except (json.JSONDecodeError, ValueError) as e:
        print(
            f"Debug: JSON parsing error for chunk {chunk_start}-{chunk_end}: {str(e)}"
        )
        print("Debug: Falling back to a default structure.")
        parsed_analysis = []

    return json.dumps({"references": parsed_analysis}, indent=2)


def process_intertextual_references(video_id, video_title, intertextual_chunks):
    consolidated_references = []
    for chunk in intertextual_chunks:
        try:
            chunk_data = json.loads(chunk)
            consolidated_references.extend(chunk_data.get("references", []))
        except json.JSONDecodeError as e:
            print(f"Error parsing intertextual chunk: {str(e)}")

    return {"references": consolidated_references}
