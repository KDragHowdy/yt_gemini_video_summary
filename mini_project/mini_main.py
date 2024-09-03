import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from mini_video_downloader import get_video_info, download_youtube_video
from mini_utils import setup_directories, clear_directory, get_transcript
from mini_error_handling import MiniVideoProcessingError
from mini_logging_config import setup_logging
from mini_video_processor import process_video

print("Mini project script started")

# Load environment variables
load_dotenv()

# Set up directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
M_INTERIM_DIR = os.path.join(BASE_DIR, "m_interim")
M_OUTPUT_DIR = os.path.join(BASE_DIR, "m_output")
M_LOG_DIR = os.path.join(BASE_DIR, "m_logs")

# Set up logging
logger = setup_logging(M_LOG_DIR)


async def mini_main():
    logger.debug("Entering mini_main function")
    start_time = time.time()
    timings = {}

    try:
        logger.info("Starting mini video processing pipeline...")
        setup_directories([M_INTERIM_DIR, M_OUTPUT_DIR, M_LOG_DIR])
        await asyncio.gather(
            clear_directory(M_INTERIM_DIR),
            clear_directory(M_OUTPUT_DIR),
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
        logger.info(f"Video info retrieved in {video_info_time:.2f} seconds")

        if not video_title or not duration:
            raise MiniVideoProcessingError("Failed to retrieve video information.")

        duration_minutes = duration / 60
        logger.info(f"Video duration: {duration_minutes:.2f} minutes")

        logger.info(f"Processing video: {video_title}")

        # Wait for transcript retrieval to complete
        transcript = await transcript_task

        # Process video
        processing_start = time.time()
        report_path = await process_video(
            video_id,
            video_title,
            duration_minutes,
            transcript,
            M_INTERIM_DIR,
            M_OUTPUT_DIR,
        )
        processing_end = time.time()
        processing_time = processing_end - processing_start
        timings["Video Processing"] = processing_time
        logger.info(f"Video processed in {processing_time:.2f} seconds")

        logger.info(f"Final report generated: {report_path}")

    except MiniVideoProcessingError as e:
        logger.error(f"MiniVideoProcessingError: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(traceback.format_exc())

    finally:
        end_time = time.time()
        total_runtime = end_time - start_time

        logger.info("\n" + "=" * 50)
        logger.info("MINI PROCESSING SUMMARY")
        logger.info("=" * 50)
        for step, duration in timings.items():
            logger.info(f"{step}: {duration:.2f} seconds")
        logger.info("-" * 50)
        logger.info(f"Total runtime: {total_runtime:.2f} seconds")
        logger.info("=" * 50)

    logger.debug("Exiting mini_main function")


if __name__ == "__main__":
    print("About to run mini_main function")
    asyncio.run(mini_main())
    print("Mini main function completed")
