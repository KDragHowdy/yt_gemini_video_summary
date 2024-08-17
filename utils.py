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
