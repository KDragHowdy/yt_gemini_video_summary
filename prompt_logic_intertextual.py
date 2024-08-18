import os
import json
from datetime import datetime
from content_generator import generate_content


def clean_json_string(json_string):
    # Find the first '{' and the last '}'
    start = json_string.find("{")
    end = json_string.rfind("}") + 1
    if start != -1 and end != 0:
        return json_string[start:end]
    return json_string


def analyze_intertextual_references(video_id, video_title, chunk_start, chunk_end):
    interim_dir = "./interim"

    shortened_title = "".join(e for e in video_title if e.isalnum())[:20]

    video_analysis_file = (
        f"wp_{shortened_title}_video_chunk_{int(chunk_start)}_{int(chunk_end)}.txt"
    )
    video_analysis_path = os.path.join(interim_dir, video_analysis_file)
    print(f"Debug: Attempting to open video analysis file: {video_analysis_path}")
    with open(video_analysis_path, "r") as f:
        video_analysis = f.read()

    transcript_analysis_file = (
        f"wp_{shortened_title}_transcript_chunk_{int(chunk_start)}_{int(chunk_end)}.txt"
    )
    transcript_analysis_path = os.path.join(interim_dir, transcript_analysis_file)
    print(
        f"Debug: Attempting to open transcript analysis file: {transcript_analysis_path}"
    )
    with open(transcript_analysis_path, "r") as f:
        transcript_analysis = f.read()

    prompt = f"""
    Analyze the following video content and transcript for intertextual references:

    Video Analysis:
    {video_analysis}

    Transcript Analysis:
    {transcript_analysis}

    Please identify and explain any references to:
    1. Literary works
    2. Philosophical concepts
    3. Historical events
    4. Scientific theories
    5. Pop culture
    6. AI technology and concepts
    7. Research papers or academic works
    8. Internet culture and memes
    9. Other notable works or ideas

    For each reference, provide:
    - The context in which it was mentioned
    - A brief explanation of the reference
    - Its significance or relevance to the speaker's point

    Format the output as a JSON object with the following structure:
    {{
        "references": [
            {{
                "type": "literary/philosophical/historical/scientific/pop_culture/ai_tech/research/internet_culture/other",
                "reference": "The actual reference",
                "context": "How it was used in the video",
                "explanation": "Brief explanation of the reference",
                "significance": "Why it's important in this context"
            }}
        ]
    }}

    Ensure that the output is a valid JSON object. Do not include any text before or after the JSON object.
    """

    intertextual_analysis = generate_content(prompt)
    print(
        f"Debug: Raw intertextual analysis content:\n{intertextual_analysis[:500]}..."
    )  # Print first 500 characters

    # Save the raw output for debugging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"wp_{shortened_title}_intertextual_raw_{int(chunk_start)}_{int(chunk_end)}_{timestamp}.txt"
    raw_path = os.path.join(interim_dir, raw_filename)
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(intertextual_analysis)
    print(f"Debug: Saved raw intertextual analysis to: {raw_path}")

    # Clean the JSON string
    cleaned_json_string = clean_json_string(intertextual_analysis)
    print(
        f"Debug: Cleaned JSON string:\n{cleaned_json_string[:500]}..."
    )  # Print first 500 characters

    try:
        parsed_analysis = json.loads(cleaned_json_string)
    except json.JSONDecodeError as e:
        print(f"Debug: JSON parsing error: {str(e)}")
        print("Debug: Falling back to a default structure.")
        parsed_analysis = {"references": []}

    # Save the processed output as JSON
    processed_filename = f"wp_{shortened_title}_intertextual_chunk_{int(chunk_start)}_{int(chunk_end)}_{timestamp}.json"
    processed_path = os.path.join(interim_dir, processed_filename)
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(parsed_analysis, f, indent=2, ensure_ascii=False)
    print(f"Debug: Saved processed intertextual analysis to: {processed_path}")

    return parsed_analysis


def process_intertextual_references(video_id, video_title, duration_minutes):
    all_references = []

    for i in range(0, int(duration_minutes), 60):
        chunk_start = i
        chunk_end = min(i + 60, duration_minutes)

        chunk_references = analyze_intertextual_references(
            video_id, video_title, chunk_start, chunk_end
        )
        all_references.extend(chunk_references.get("references", []))

    return all_references


# Example usage
if __name__ == "__main__":
    video_id = "example_video_id"
    video_title = "The Philosophy of Large Language Models"
    duration_minutes = 120  # Example duration

    all_references = process_intertextual_references(
        video_id, video_title, duration_minutes
    )
    print(json.dumps(all_references, indent=2, ensure_ascii=False))
