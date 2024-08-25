import os
import sys
import json
import shutil
from dotenv import load_dotenv
from video_downloader import get_video_info, download_youtube_video
from video_processor import process_video
from final_report_generator import generate_final_report
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


def clear_directory(directory):
    print(f"Clearing {directory} directory...")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
    print(f"{directory} directory cleared.")


def main():
    try:
        setup_directories([INPUT_DIR, OUTPUT_DIR, INTERIM_DIR])
        clear_directory(INTERIM_DIR)  # Clear interim directory at the start
        clear_directory(INPUT_DIR)  # Clear input directory at the start
        clear_directory(OUTPUT_DIR)  # Clear output directory at the start

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

        # Generate the final report
        generate_final_report(video_title)

        print("Video processing and final report generation completed successfully.")

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
