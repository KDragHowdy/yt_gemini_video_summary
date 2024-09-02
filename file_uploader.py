import google.generativeai as genai
import asyncio
import time
import os
from api_statistics import api_stats
import logging

logger = logging.getLogger(__name__)


async def upload_video(video_path):
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)
    logger.info(f"File details: Path: {video_path}, Size: {file_size_mb:.2f} MB")

    logger.info(f"Starting upload for {video_path}...")
    try:
        file = await asyncio.to_thread(genai.upload_file, path=video_path)
        logger.info(f"Upload completed: {file.uri}")
        await api_stats.record_api_interaction("File Upload")
        return file, file.uri
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise


async def check_video_status(video_file):
    max_retries = 10
    retry_delay = 15
    for _ in range(max_retries):
        if video_file.state.name == "PROCESSING":
            logger.debug(
                f"Video {video_file.name} is still processing. Checking again in 15 seconds..."
            )
            await asyncio.sleep(retry_delay)
            video_file = await asyncio.to_thread(genai.get_file, video_file.name)
        else:
            break

    if video_file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {video_file.state.name}")
    elif video_file.state.name != "ACTIVE":
        raise ValueError(
            f"File processing did not complete successfully: {video_file.state.name}"
        )

    logger.info(f"Video {video_file.name} is now active and ready for use.")
    return video_file
