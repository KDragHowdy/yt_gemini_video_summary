import os
import sys
from dotenv import load_dotenv
from video_downloader import get_video_info, download_youtube_video
from video_processor import process_video
from report_generator import generate_and_save_reports
from utils import setup_directories
from error_handling import VideoProcessingError
from prompt_logic_intertextual import process_intertextual_references

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
        print("Debug: Starting main function")
        setup_directories([INPUT_DIR, OUTPUT_DIR, INTERIM_DIR])
        print("Debug: Directories set up")

        video_id = input("Enter the YouTube video ID: ")
        print(f"Debug: Video ID entered: {video_id}")

        print("Debug: Getting video info")
        video_title, duration = get_video_info(video_id)
        print(
            f"Debug: Video info retrieved - Title: {video_title}, Duration: {duration}"
        )

        if not video_title or not duration:
            raise VideoProcessingError("Failed to retrieve video information.")

        duration_minutes = duration / 60
        print(f"Debug: Duration in minutes: {duration_minutes}")

        if duration_minutes > 60:
            proceed = input(
                f"The video '{video_title}' is {duration_minutes:.2f} minutes long. Do you want to continue? (y/n): "
            )
            if proceed.lower() != "y":
                print("Operation cancelled.")
                return

        print(f"Processing video: {video_title}")
        print("Debug: Downloading YouTube video")
        video_path = download_youtube_video(video_id, INPUT_DIR)
        if not video_path:
            raise VideoProcessingError("Failed to download video.")
        print(f"Debug: Video downloaded to {video_path}")

        print("Debug: Starting video processing")
        summary_chunks, intertextual_chunks = process_video(
            video_path, video_id, video_title, duration_minutes
        )
        print("Debug: Video processing completed")

        print("Debug: Processing intertextual references")
        intertextual_references = process_intertextual_references(
            video_id, video_title, intertextual_chunks
        )

        print("Debug: Generating and saving reports")
        generate_and_save_reports(
            video_id, video_title, summary_chunks, intertextual_references, OUTPUT_DIR
        )

        print("Video processing completed successfully.")

    except VideoProcessingError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print(f"Debug: Exception type: {type(e)}")
        print(f"Debug: Exception args: {e.args}")
        import traceback

        print("Debug: Full traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
