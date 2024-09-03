import os
import asyncio
import shutil
from youtube_transcript_api import YouTubeTranscriptApi


def setup_directories(directories):
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
    print(f"Directories set up: {', '.join(directories)}")


async def clear_directory(directory):
    print(f"Clearing {directory} directory...")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                await asyncio.to_thread(shutil.rmtree, file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
    print(f"{directory} directory cleared.")


async def get_transcript(video_id):
    try:
        transcript = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript, video_id
        )
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return ""