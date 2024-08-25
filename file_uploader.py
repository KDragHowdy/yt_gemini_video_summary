import google.generativeai as genai
import time
import os
import datetime

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=GEMINI_API_KEY)


def upload_video(video_path):
    file_size = os.path.getsize(video_path)  # Get file size in bytes
    file_size_mb = file_size / (1024 * 1024)  # Convert to megabytes
    print(f"File details: Path: {video_path}, Size: {file_size_mb:.2f} MB")

    start_time = time.time()  # Start the timer

    print(f"Uploading file...")
    video_file = genai.upload_file(path=video_path)

    end_time = time.time()  # End the timer
    upload_duration = end_time - start_time  # Calculate the duration in seconds

    print(f"Completed upload: {video_file.uri}")
    print(f"Upload duration: {upload_duration:.2f} seconds")

    return video_file


def wait_for_file_active(video_file):
    while video_file.state.name == "PROCESSING":
        print(".", end="")
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {video_file.state.name}")

    return video_file
