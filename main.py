import time
import os
import asyncio
import logging
from dotenv import load_dotenv
from video_downloader import get_video_info, download_youtube_video
from video_processor import process_video
from new_final_report_generator import generate_final_report
from utils import setup_directories, clear_directory, get_transcript, debug_print
from error_handling import VideoProcessingError
from api_statistics import api_stats

print("Script started")

# Load environment variables
load_dotenv()

# Set up directories
BASE_DIR = r"C:\Users\kevin\repos\yt_gemini_video_summary"
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
INTERIM_DIR = os.path.join(BASE_DIR, "interim")

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(BASE_DIR, "video_processing.log"),
    filemode="w",
)

# Add console handler to display logs in console as well
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger("").addHandler(console_handler)

logger = logging.getLogger(__name__)


async def main():
    logger.debug("Entering main function")
    start_time = time.time()
    timings = {}

    try:
        logger.info("Starting video processing pipeline...")
        setup_directories([INPUT_DIR, OUTPUT_DIR, INTERIM_DIR])
        await asyncio.gather(
            clear_directory(INTERIM_DIR),
            clear_directory(INPUT_DIR),
            clear_directory(OUTPUT_DIR),
        )

        video_id = input("Enter the YouTube video ID: ")
        logger.debug(f"Received video ID: {video_id}")

        # Start transcript retrieval early
        transcript_task = asyncio.create_task(get_transcript(video_id))

        # Timer for video info retrieval
        logger.info("Retrieving video information...")
        video_info_start = time.time()
        video_title, duration = await get_video_info(video_id)
        video_info_end = time.time()
        video_info_time = video_info_end - video_info_start
        timings["Video Info Retrieval"] = video_info_time
        await api_stats.record_process(
            "Video Info Retrieval", video_info_start, video_info_end
        )
        logger.info(f"Video info retrieved in {video_info_time:.2f} seconds")

        if not video_title or not duration:
            raise VideoProcessingError("Failed to retrieve video information.")

        duration_minutes = duration / 60
        logger.info(f"Video duration: {duration_minutes:.2f} minutes")

        if duration_minutes > 60:
            proceed = input(
                f"The video '{video_title}' is longer than an hour. Do you want to continue? (y/n): "
            )
            if proceed.lower() != "y":
                logger.info("Operation cancelled.")
                return

        logger.info(f"Processing video: {video_title}")

        # Timer for video download
        logger.info("Downloading video...")
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
        logger.info(f"Video downloaded in {download_time:.2f} seconds")

        if not video_chunks:
            raise VideoProcessingError("Failed to download video.")

        # Wait for transcript retrieval to complete
        transcript = await transcript_task

        # Timer for video processing
        logger.info("Processing video chunks...")
        processing_start = time.time()
        (
            consolidated_intertextual,
            consolidated_video,
            consolidated_transcript,
        ) = await process_video(
            video_chunks, video_id, video_title, duration_minutes, transcript
        )
        processing_end = time.time()
        processing_time = processing_end - processing_start
        timings["Video Processing"] = processing_time
        await api_stats.record_process(
            "Video Processing", processing_start, processing_end
        )
        logger.info(f"Video processed in {processing_time:.2f} seconds")

        # Timer for final report generation and API statistics
        logger.info("Generating final report and API statistics...")
        report_start = time.time()

        video_info = {
            "id": video_id,
            "title": video_title,
            "date": video_date,
            "channel": channel_name,
            "speaker": speaker_name,
            "duration": duration_minutes,
        }

        final_report_task = asyncio.create_task(generate_final_report(video_info))
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
        logger.info(
            f"Final report and API statistics generated in {report_time:.2f} seconds"
        )

        # Save the API statistics report
        stats_file = os.path.join(OUTPUT_DIR, "api_statistics_report.txt")
        await api_stats.save_report(stats_file)

        logger.info(f"Final report generated: {final_report}")
        logger.info(f"API statistics report saved to: {stats_file}")

        # Print API statistics to console
        logger.info("API Statistics Summary:")
        logger.info(stats_report)

        logger.info(
            "Video processing and final report generation completed successfully."
        )

    except VideoProcessingError as e:
        logger.error(f"VideoProcessingError: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(traceback.format_exc())

    finally:
        end_time = time.time()
        total_runtime = end_time - start_time
        await api_stats.record_process("Total Script Runtime", start_time, end_time)

        logger.info("\n" + "=" * 50)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 50)
        for step, duration in timings.items():
            logger.info(f"{step}: {duration:.2f} seconds")
        logger.info("-" * 50)
        logger.info(f"Total runtime: {total_runtime:.2f} seconds")
        logger.info("=" * 50)

    logger.debug("Exiting main function")


if __name__ == "__main__":
    print("About to run main function")
    asyncio.run(main())
    print("Main function completed")
