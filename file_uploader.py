# file_uploader.py

import google.generativeai as genai
import asyncio
import time
import os
from api_statistics import api_stats


async def upload_video(video_path):
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"File details: Path: {video_path}, Size: {file_size_mb:.2f} MB")

    print(f"Starting upload for {video_path}...")
    await api_stats.record_api_interaction("File Upload")
    video_file = await asyncio.to_thread(genai.upload_file, path=video_path)
    print(f"Upload started: {video_file.uri}")

    return video_file


async def check_video_status(video_file):
    max_retries = 30
    retry_delay = 60  # Check every 60 seconds
    for _ in range(max_retries):
        if video_file.state.name == "PROCESSING":
            print(
                f"Video {video_file.name} is still processing. Checking again in 60 seconds..."
            )
            await asyncio.sleep(retry_delay)
            await api_stats.record_api_interaction("File Status Check")
            video_file = await asyncio.to_thread(genai.get_file, video_file.name)
        else:
            break

    if video_file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {video_file.state.name}")
    elif video_file.state.name != "ACTIVE":
        raise ValueError(
            f"File processing did not complete successfully: {video_file.state.name}"
        )

    print(f"Video {video_file.name} is now active and ready for use.")
    return video_file
