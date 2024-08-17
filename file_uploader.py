import google.generativeai as genai
import time
import os

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=GEMINI_API_KEY)


def upload_video(video_path):
    print("Uploading file...")
    video_file = genai.upload_file(path=video_path)
    print(f"Completed upload: {video_file.uri}")
    return video_file


def wait_for_file_active(video_file):
    while video_file.state.name == "PROCESSING":
        print(".", end="")
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {video_file.state.name}")

    return video_file
