import os
import json
from datetime import datetime
import google.generativeai as genai

# Configure Gemini API (you'll need to set up your API key)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    "gemini-1.5-pro", generation_config={"response_mime_type": "application/json"}
)


def read_work_product(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def analyze_implied_knowledge(video_analysis, transcript_analysis):
    prompt = f"""
    Analyze the following video content description and transcript for implied knowledge:

    Video Content Description:
    {video_analysis}

    Transcript:
    {transcript_analysis}

    Identify:
    1. Unstated assumptions in the speaker's arguments
    2. Knowledge gaps the speaker doesn't address but assumes the audience understands
    3. Level of expertise or familiarity with topics expected from the audience
    4. Jargon or specialized vocabulary used without explanation

    Format the output as a JSON array of objects with the following structure:
    [
        {{
            "type": "assumption/knowledge_gap/expertise_level/jargon",
            "context": "How it appears in the video",
            "explanation": "What knowledge is implied",
            "significance": "Why it's important for understanding the content"
        }}
    ]

    Ensure that the output is a valid JSON array. Do not include any text before or after the JSON array.
    """

    response = model.generate_content(prompt)
    return response.text


def save_implied_knowledge_analysis(analysis, video_id, chunk_start, chunk_end):
    interim_dir = "./interim"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wp_{video_id}_implied_knowledge_chunk_{chunk_start}_{chunk_end}_{timestamp}.json"

    file_path = os.path.join(interim_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(analysis)

    print(f"Saved implied knowledge analysis to: {file_path}")
    return filename


def process_implied_knowledge(video_id):
    interim_dir = "./interim"

    # Find all chunk files for this video ID
    video_chunks = [
        f
        for f in os.listdir(interim_dir)
        if f.startswith(f"wp_{video_id}_video_chunk_")
    ]
    transcript_chunks = [
        f
        for f in os.listdir(interim_dir)
        if f.startswith(f"wp_{video_id}_transcript_chunk_")
    ]

    if not video_chunks or not transcript_chunks:
        print(f"Error: No chunk files found for video ID {video_id}")
        return

    for video_file in video_chunks:
        # Extract chunk start and end from filename
        chunk_info = video_file.split("_chunk_")[1].split(".")[0]
        chunk_start, chunk_end = chunk_info.split("_")

        # Find corresponding transcript file
        transcript_file = (
            f"wp_{video_id}_transcript_chunk_{chunk_start}_{chunk_end}.txt"
        )

        if transcript_file not in transcript_chunks:
            print(f"Warning: No matching transcript file for {video_file}")
            continue

        video_analysis = read_work_product(os.path.join(interim_dir, video_file))
        transcript_analysis = read_work_product(
            os.path.join(interim_dir, transcript_file)
        )

        implied_knowledge_analysis = analyze_implied_knowledge(
            video_analysis, transcript_analysis
        )
        save_implied_knowledge_analysis(
            implied_knowledge_analysis, video_id, chunk_start, chunk_end
        )

    print("Implied knowledge analysis completed for all available chunks.")


if __name__ == "__main__":
    # Test the module
    video_id = "Imanaccelerationist"

    process_implied_knowledge(video_id)
