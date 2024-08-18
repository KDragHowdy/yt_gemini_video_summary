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
    for file in sorted(os.listdir(interim_dir)):
        if file.startswith(f"wp_{shortened_title}_{analysis_type}_chunk_"):
            with open(os.path.join(interim_dir, file), "r") as f:
                consolidated_content += f.read() + "\n\n"

    consolidated_filename = f"wp_{shortened_title}_{analysis_type}_consolidated.txt"
    with open(os.path.join(interim_dir, consolidated_filename), "w") as f:
        f.write(consolidated_content)

    print(f"Consolidated {analysis_type} saved as {consolidated_filename}")
