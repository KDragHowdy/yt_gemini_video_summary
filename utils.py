import os
from youtube_transcript_api import YouTubeTranscriptApi


def setup_directories(directories):
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)


def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return ""


def consolidate_work_products(video_id, video_title, analysis_type):
    interim_dir = "./interim"
    shortened_title = "".join(e for e in video_title if e.isalnum())[:20]

    consolidated_content = ""
    chunk_files = []

    # Collect all relevant chunk files
    for file in os.listdir(interim_dir):
        if file.startswith(
            f"wp_{shortened_title}_{analysis_type}_chunk_"
        ) and file.endswith(".txt"):
            chunk_files.append(file)

    if not chunk_files:
        print(f"Warning: No chunk files found for {analysis_type}")
        return ""

    # Sort chunk files to ensure correct order
    chunk_files.sort(key=lambda x: int(x.split("_chunk_")[1].split("-")[0]))

    # Combine content from all chunk files
    for file in chunk_files:
        with open(os.path.join(interim_dir, file), "r", encoding="utf-8") as f:
            content = f.read()
            consolidated_content += content + "\n\n"

    if consolidated_content:
        consolidated_filename = f"wp_{shortened_title}_{analysis_type}_consolidated.txt"
        with open(
            os.path.join(interim_dir, consolidated_filename), "w", encoding="utf-8"
        ) as f:
            f.write(consolidated_content)
        print(f"Consolidated {analysis_type} saved as {consolidated_filename}")
    else:
        print(f"Warning: No content found to consolidate for {analysis_type}")

    return consolidated_content
