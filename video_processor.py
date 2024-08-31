import asyncio
import time
import logging
from typing import List, Tuple
from file_uploader import upload_video, check_video_status
from content_generator import (
    analyze_video_content,
    analyze_transcript,
    save_interim_work_product,
)
from prompt_logic_intertextual import analyze_intertextual_references
from api_statistics import api_stats
from models import get_gemini_flash_model_text
from utils import debug_print

# Set up logging
logger = logging.getLogger(__name__)


async def rate_limited_api_call(func, *args, **kwargs):
    await api_stats.wait_for_rate_limit()
    logger.debug(f"Making rate-limited API call to {func.__name__}")
    try:
        result = await func(*args, **kwargs)
        logger.debug(f"Completed rate-limited API call to {func.__name__}")
        return result
    except Exception as e:
        logger.error(f"Error in rate_limited_api_call to {func.__name__}: {str(e)}")
        raise


async def process_video(
    video_chunks: List[str],
    video_id: str,
    video_title: str,
    duration_minutes: float,
    transcript: str,
) -> Tuple[str, str, str]:
    start_time = time.time()
    logger.info("Starting video processing")

    # Upload all video chunks at the beginning
    upload_tasks = [upload_video(chunk_path) for chunk_path in video_chunks]
    uploaded_files = await asyncio.gather(*upload_tasks)
    logger.info("All video chunks uploaded")

    async def process_chunk(
        chunk_path: str,
        chunk_start: float,
        chunk_end: float,
        chunk_transcript: str,
        video_file,
    ):
        logger.debug(f"Processing chunk {chunk_start}-{chunk_end}")

        try:
            # Perform transcript and intertextual analyses immediately
            logger.debug(
                f"Initiating transcript analysis for chunk {chunk_start}-{chunk_end}"
            )
            try:
                await api_stats.record_api_interaction(
                    f"Transcript Analysis Init {chunk_start}-{chunk_end}"
                )
            except Exception as e:
                logger.error(f"Error recording API interaction: {str(e)}")
            transcript_analysis_task = rate_limited_api_call(
                analyze_transcript, chunk_transcript, chunk_start, chunk_end
            )

            logger.debug(
                f"Initiating intertextual analysis for chunk {chunk_start}-{chunk_end}"
            )
            try:
                await api_stats.record_api_interaction(
                    f"Intertextual Analysis Init {chunk_start}-{chunk_end}"
                )
            except Exception as e:
                logger.error(f"Error recording API interaction: {str(e)}")
            intertextual_analysis_task = rate_limited_api_call(
                analyze_intertextual_references,
                chunk_transcript,
                chunk_start,
                chunk_end,
            )

            transcript_analysis, intertextual_analysis = await asyncio.gather(
                transcript_analysis_task, intertextual_analysis_task
            )

            # Save interim work products for transcript and intertextual analyses
            await asyncio.gather(
                save_interim_work_product(
                    transcript_analysis,
                    video_id,
                    video_title,
                    f"transcript_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
                ),
                save_interim_work_product(
                    intertextual_analysis,
                    video_id,
                    video_title,
                    f"intertextual_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
                ),
            )

            # Wait for video file to be ready
            video_file = await check_video_status(video_file)

            # Perform video content analysis
            logger.debug(
                f"Initiating video content analysis for chunk {chunk_start}-{chunk_end}"
            )
            try:
                await api_stats.record_api_interaction(
                    f"Video Content Analysis Init {chunk_start}-{chunk_end}"
                )
            except Exception as e:
                logger.error(f"Error recording API interaction: {str(e)}")
            video_analysis = await rate_limited_api_call(
                analyze_video_content, video_file, chunk_start, chunk_end
            )

            # Save interim work product for video analysis
            await save_interim_work_product(
                video_analysis,
                video_id,
                video_title,
                f"video_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
            )

            logger.debug(f"Chunk {chunk_start}-{chunk_end} processing complete")
            return video_analysis, transcript_analysis, intertextual_analysis
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_start}-{chunk_end}: {str(e)}")
            return f"Error: {str(e)}", f"Error: {str(e)}", f"Error: {str(e)}"

    chunk_tasks = []
    for i, (chunk_path, video_file) in enumerate(zip(video_chunks, uploaded_files)):
        chunk_start = i * 10
        chunk_end = min((i + 1) * 10, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]
        chunk_tasks.append(
            process_chunk(
                chunk_path, chunk_start, chunk_end, chunk_transcript, video_file
            )
        )

    results = await asyncio.gather(*chunk_tasks)

    video_analyses, transcript_analyses, intertextual_analyses = zip(*results)

    consolidated_video = await consolidate_analyses(
        video_analyses, video_id, video_title, "video"
    )
    consolidated_transcript = await consolidate_analyses(
        transcript_analyses, video_id, video_title, "transcript"
    )
    consolidated_intertextual = await consolidate_analyses(
        intertextual_analyses, video_id, video_title, "intertextual"
    )

    end_time = time.time()
    try:
        await api_stats.record_process("process_video", start_time, end_time)
    except Exception as e:
        logger.error(f"Error recording process: {str(e)}")

    logger.info("Video processing complete")
    return consolidated_intertextual, consolidated_video, consolidated_transcript


async def consolidate_analyses(
    analyses: List[str], video_id: str, video_title: str, analysis_type: str
) -> str:
    consolidated = "\n\n".join(analyses)
    prompt = f"Consolidate and summarize the following {analysis_type} analyses:\n\n{consolidated}"

    logger.debug(f"Initiating consolidation of {analysis_type} analyses")
    try:
        await api_stats.record_api_interaction(f"Consolidate {analysis_type} Analysis")
    except Exception as e:
        logger.error(f"Error recording API interaction: {str(e)}")
    model = await get_gemini_flash_model_text()
    response = await rate_limited_api_call(model.generate_content_async, prompt)

    consolidated_analysis = response.text
    await save_interim_work_product(
        consolidated_analysis,
        video_id,
        video_title,
        f"consolidated_{analysis_type}_analysis",
    )

    return consolidated_analysis
