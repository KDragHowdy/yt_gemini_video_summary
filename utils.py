import json
import os
from youtube_transcript_api import YouTubeTranscriptApi
import aiofiles
import time
import asyncio
import shutil
import logging

logger = logging.getLogger(__name__)

start_time = time.time()


def setup_directories(directories):
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
    logger.info(f"Directories set up: {', '.join(directories)}")


async def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        return ""


async def clear_directory(directory):
    logger.info(f"Clearing {directory} directory...")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                await asyncio.to_thread(shutil.rmtree, file_path)
        except Exception as e:
            logger.error(f"Failed to delete {file_path}. Reason: {e}")
    logger.info(f"{directory} directory cleared.")


def debug_print(message):
    current_time = time.time()
    elapsed_time = current_time - start_time
    logger.debug(f"[{elapsed_time:.2f}s] {message}")
