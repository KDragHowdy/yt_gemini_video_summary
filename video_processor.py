import asyncio
import time
import logging
from typing import List, Tuple
from api_statistics import api_stats
from file_uploader import upload_video, check_video_status
from content_generator import (
    analyze_video_content,
    analyze_transcript,
    save_interim_work_product,
)
from prompt_logic_intertextual import analyze_intertextual_references
from models import get_gemini_flash_model_text, get_gemini_pro_model_text

logger = logging.getLogger(__name__)


async def rate_limited_api_call(func, *args, **kwargs):
    if func.__name__ in [
        "generate_integrated_report",
        "generate_structured_elements_appendix",
        "generate_intertextual_analysis_appendix",
    ]:
        model_type = "pro"
    else:
        model_type = "flash"

    start_time = time.time()
    await api_stats.wait_for_rate_limit(model_type)
    result = await func(*args, **kwargs)

    if hasattr(result, "usage_metadata"):
        logger.debug(f"Usage metadata: {result.usage_metadata}")
    else:
        logger.warning("Response object does not have usage_metadata attribute")
        if isinstance(result, str):
            logger.debug("Result is a string, likely JSON content")
        logger.debug(f"Result type: {type(result)}")

    await api_stats.record_call(
        module="video_processor",
        function=func.__name__,
        start_time=start_time,
        response=result,
        model_type=model_type,
    )
    return result


async def process_video(
    video_chunks: List[str],
    video_id: str,
    video_title: str,
    duration_minutes: float,
    transcript: str,
) -> Tuple[str, str, str]:
    start_time = time.time()
    logger.info("Starting video processing")

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
            async with asyncio.timeout(300):  # 5-minute timeout per chunk
                transcript_analysis_task = rate_limited_api_call(
                    analyze_transcript, chunk_transcript, chunk_start, chunk_end
                )
                intertextual_analysis_task = rate_limited_api_call(
                    analyze_intertextual_references,
                    chunk_transcript,
                    chunk_start,
                    chunk_end,
                )

                transcript_analysis, intertextual_analysis = await asyncio.gather(
                    transcript_analysis_task, intertextual_analysis_task
                )

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

                video_file = await check_video_status(video_file)

                video_analysis = await rate_limited_api_call(
                    analyze_video_content, video_file, chunk_start, chunk_end
                )

                await save_interim_work_product(
                    video_analysis,
                    video_id,
                    video_title,
                    f"video_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
                )

                logger.debug(f"Chunk {chunk_start}-{chunk_end} processing complete")
                return video_analysis, transcript_analysis, intertextual_analysis
        except asyncio.TimeoutError:
            logger.error(f"Timeout processing chunk {chunk_start}-{chunk_end}")
            return f"Error: Timeout", f"Error: Timeout", f"Error: Timeout"
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

    async def wait_and_consolidate(chunk_tasks, analysis_type):
        analyses = []
        for task in asyncio.as_completed(chunk_tasks):
            result = await task
            if analysis_type == "transcript":
                analyses.append(result[1])  # Transcript analysis is the second item
            elif analysis_type == "intertextual":
                analyses.append(result[2])  # Intertextual analysis is the third item
            elif analysis_type == "video":
                analyses.append(result[0])  # Video analysis is the first item
            if len(analyses) == len(chunk_tasks):
                return await consolidate_analyses(
                    analyses, video_id, video_title, analysis_type
                )

    transcript_tasks = [asyncio.create_task(task) for task in chunk_tasks]
    intertextual_tasks = [asyncio.create_task(task) for task in chunk_tasks]
    video_tasks = [asyncio.create_task(task) for task in chunk_tasks]

    transcript_consolidation_task = asyncio.create_task(
        wait_and_consolidate(transcript_tasks, "transcript")
    )
    intertextual_consolidation_task = asyncio.create_task(
        wait_and_consolidate(intertextual_tasks, "intertextual")
    )
    video_consolidation_task = asyncio.create_task(
        wait_and_consolidate(video_tasks, "video")
    )

    results = await asyncio.gather(*chunk_tasks)

    (
        consolidated_transcript,
        consolidated_intertextual,
        consolidated_video,
    ) = await asyncio.gather(
        transcript_consolidation_task,
        intertextual_consolidation_task,
        video_consolidation_task,
    )

    end_time = time.time()
    await api_stats.record_process("process_video", start_time, end_time)

    logger.info("Video processing complete")
    return consolidated_intertextual, consolidated_video, consolidated_transcript


async def consolidate_analyses(
    analyses: List[str], video_id: str, video_title: str, analysis_type: str
) -> str:
    consolidated = "\n\n".join(analyses)
    prompt = f"Consolidate and summarize the following {analysis_type} analyses:\n\n{consolidated}"

    logger.debug(f"Initiating consolidation of {analysis_type} analyses")
    model = await get_gemini_pro_model_text()
    response = await rate_limited_api_call(model.generate_content_async, prompt)

    consolidated_analysis = response.text
    await save_interim_work_product(
        consolidated_analysis,
        video_id,
        video_title,
        f"consolidated_{analysis_type}_analysis",
    )

    return consolidated_analysis
