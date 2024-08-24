import os
import sys
import json
from dotenv import load_dotenv
from video_downloader import get_video_info, download_youtube_video
from video_processor import process_video
from generate_and_save_reports import generate_and_save_reports
from utils import setup_directories
from error_handling import VideoProcessingError

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Load environment variables
load_dotenv()

# Set up directories
BASE_DIR = r"C:\Users\kevin\repos\yt_gemini_video_summary"
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
INTERIM_DIR = os.path.join(BASE_DIR, "interim")


def main():
    try:
        setup_directories([INPUT_DIR, OUTPUT_DIR, INTERIM_DIR])

        video_id = input("Enter the YouTube video ID: ")
        video_title, duration = get_video_info(video_id)

        if not video_title or not duration:
            raise VideoProcessingError("Failed to retrieve video information.")

        duration_minutes = duration / 60
        print(f"Video duration: {duration_minutes:.2f} minutes")

        if duration_minutes > 60:
            proceed = input(
                f"The video '{video_title}' is longer than an hour. Do you want to continue? (y/n): "
            )
            if proceed.lower() != "y":
                print("Operation cancelled.")
                return

        print(f"Processing video: {video_title}")
        chunk_duration = 10 * 60  # 10 minutes in seconds
        video_chunks = download_youtube_video(video_id, INPUT_DIR, chunk_duration)
        if not video_chunks:
            raise VideoProcessingError("Failed to download video.")

        summary_chunks, intertextual_chunks, video_analyses = process_video(
            video_chunks, video_id, video_title, duration_minutes
        )

        generate_and_save_reports(
            video_id,
            video_title,
            summary_chunks,
            intertextual_chunks,
            video_analyses,
            OUTPUT_DIR,
        )

        print("Video processing completed successfully.")

    except VideoProcessingError as e:
        print(f"VideoProcessingError: {str(e)}")
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
    sys.exit(1)


if __name__ == "__main__":
    main()
