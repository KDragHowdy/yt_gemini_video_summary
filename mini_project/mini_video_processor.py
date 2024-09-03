import asyncio
import time
import logging
from typing import List, Tuple
from mini_video_downloader import download_youtube_video
from structured_element_capture import process_structured_elements
from mini_error_handling import handle_mini_exceptions, MiniVideoProcessingError

logger = logging.getLogger(__name__)


@handle_mini_exceptions
async def process_video(
    video_id: str,
    video_title: str,
    duration_minutes: float,
    transcript: str,
    interim_dir: str,
    output_dir: str,
) -> str:
    start_time = time.time()
    logger.info("Starting mini video processing")

    try:
        # Download video chunks
        video_chunks, _, _, _, _ = await download_youtube_video(video_id, interim_dir)
        logger.info("Video chunks downloaded")

        if not video_chunks:
            raise MiniVideoProcessingError("Failed to download video chunks.")

        # Process structured elements
        report_path, report_content = await process_structured_elements(
            video_chunks,
            video_id,
            video_title,
            duration_minutes,
            transcript,
            interim_dir,
            output_dir,
        )

        if report_content != "No structured elements found.":
            logger.info("Structured elements found and processed")
            logger.info(f"Mini final picture report generated: {report_path}")
        else:
            logger.info("No structured elements found in the video")

        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(f"Mini video processing completed in {processing_time:.2f} seconds")

        return report_path

    except Exception as e:
        logger.error(f"Error in mini video processing: {str(e)}")
        raise MiniVideoProcessingError(f"Failed to process video: {str(e)}")
