# main.py

import time
import os
import sys
import json
import asyncio
import aiofiles
from dotenv import load_dotenv
from video_downloader import get_video_info, download_youtube_video
from video_processor import process_video
from final_report_generator import generate_final_report
from utils import setup_directories, clear_directory, get_transcript
from error_handling import VideoProcessingError
from api_statistics import api_stats

# Load environment variables
load_dotenv()

# Set up directories
BASE_DIR = r"C:\Users\kevin\repos\yt_gemini_video_summary"
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
INTERIM_DIR = os.path.join(BASE_DIR, "interim")


async def main():
    start_time = time.time()
    timings = {}

    try:
        print("Starting video processing pipeline...")
        setup_directories([INPUT_DIR, OUTPUT_DIR, INTERIM_DIR])
        await asyncio.gather(
            clear_directory(INTERIM_DIR),
            clear_directory(INPUT_DIR),
            clear_directory(OUTPUT_DIR),
        )

        video_id = input("Enter the YouTube video ID: ")

        # Timer for video info retrieval
        print("\nRetrieving video information...")
        video_info_start = time.time()
        video_title, duration = await get_video_info(video_id)
        video_info_end = time.time()
        video_info_time = video_info_end - video_info_start
        timings["Video Info Retrieval"] = video_info_time
        await api_stats.record_process(
            "Video Info Retrieval", video_info_start, video_info_end
        )
        print(f"Video info retrieved in {video_info_time:.2f} seconds")

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

        print(f"\nProcessing video: {video_title}")

        # Start transcript retrieval early
        transcript_task = asyncio.create_task(get_transcript(video_id))

        # Timer for video download
        print("Downloading video...")
        download_start = time.time()
        (
            video_chunks,
            video_title,
            video_date,
            channel_name,
            speaker_name,
        ) = await download_youtube_video(video_id, INPUT_DIR)
        download_end = time.time()
        download_time = download_end - download_start
        timings["Video Download"] = download_time
        await api_stats.record_process("Video Download", download_start, download_end)
        print(f"Video downloaded in {download_time:.2f} seconds")

        if not video_chunks:
            raise VideoProcessingError("Failed to download video.")

        # Wait for transcript retrieval to complete
        transcript = await transcript_task

        # Timer for video processing
        print("\nProcessing video chunks...")
        processing_start = time.time()
        intertextual_chunks, video_analyses = await process_video(
            video_chunks, video_id, video_title, duration_minutes, transcript
        )
        processing_end = time.time()
        processing_time = processing_end - processing_start
        timings["Video Processing"] = processing_time
        await api_stats.record_process(
            "Video Processing", processing_start, processing_end
        )
        print(f"Video processed in {processing_time:.2f} seconds")

        # Timer for final report generation and API statistics
        print("\nGenerating final report and API statistics...")
        report_start = time.time()

        final_report_task = asyncio.create_task(
            generate_final_report(
                video_title=video_title,
                video_date=video_date,
                channel_name=channel_name,
                speaker_name=speaker_name,
                video_duration_minutes=duration_minutes,
            )
        )

        stats_report_task = asyncio.create_task(api_stats.generate_report_async())

        # Wait for both tasks to complete
        final_report, stats_report = await asyncio.gather(
            final_report_task, stats_report_task
        )

        report_end = time.time()
        report_time = report_end - report_start
        timings["Final Report Generation"] = report_time
        await api_stats.record_process(
            "Final Report Generation", report_start, report_end
        )
        print(f"Final report and API statistics generated in {report_time:.2f} seconds")

        # Save the API statistics report
        stats_file = os.path.join(OUTPUT_DIR, "api_statistics_report.txt")
        await api_stats.save_report(stats_file)

        print(f"Final report generated: {final_report}")
        print(f"API statistics report saved to: {stats_file}")

        # Print API statistics to console
        print("\nAPI Statistics Summary:")
        print(stats_report)

        print("\nVideo processing and final report generation completed successfully.")

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

    finally:
        end_time = time.time()
        total_runtime = end_time - start_time
        await api_stats.record_process("Total Script Runtime", start_time, end_time)

        print("\n" + "=" * 50)
        print("PROCESSING SUMMARY")
        print("=" * 50)
        for step, duration in timings.items():
            print(f"{step}: {duration:.2f} seconds")
        print("-" * 50)
        print(f"Total runtime: {total_runtime:.2f} seconds")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
