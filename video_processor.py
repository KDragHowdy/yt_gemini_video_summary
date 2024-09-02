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
    logger.info(f"Attempting API call for {func.__name__}")
    await api_stats.wait_for_rate_limit(model_type)
    logger.info(f"Rate limit check passed for {func.__name__}")
    result = await func(*args, **kwargs)
    logger.info(f"API call completed for {func.__name__}")

    if hasattr(result, "usage_metadata"):
        logger.debug(f"Usage metadata: {result.usage_metadata}")
    else:
        logger.warning("Response object does not have usage_metadata attribute")
        if isinstance(result, str):
            logger.debug(f"Result (first 200 chars): {result[:200]}")
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

    # Upload video chunks
    upload_tasks = [upload_video(chunk_path) for chunk_path in video_chunks]
    uploaded_files_and_uris = await asyncio.gather(*upload_tasks)
    uploaded_files, uploaded_uris = zip(*uploaded_files_and_uris)
    logger.info("All video chunks uploaded")

    # Wait for files to become active
    check_tasks = [check_video_status(file) for file in uploaded_files]
    active_files = await asyncio.gather(*check_tasks)
    logger.info("All video chunks are active and ready for processing")

    # Prepare chunk information
    chunk_infos = []
    chunk_transcripts = []
    for i, _ in enumerate(video_chunks):
        chunk_start = i * 10
        chunk_end = min((i + 1) * 10, duration_minutes)
        chunk_infos.append((chunk_start, chunk_end))
        chunk_transcripts.append(
            transcript[int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)]
        )

    # Create tasks for all analyses
    video_tasks = [
        analyze_video_content(file, *chunk_info)
        for file, chunk_info in zip(active_files, chunk_infos)
    ]
    transcript_tasks = [
        analyze_transcript(chunk_transcript, *chunk_info)
        for chunk_transcript, chunk_info in zip(chunk_transcripts, chunk_infos)
    ]
    intertextual_tasks = [
        analyze_intertextual_references(chunk_transcript, *chunk_info)
        for chunk_transcript, chunk_info in zip(chunk_transcripts, chunk_infos)
    ]

    # Wait for all analyses to complete
    video_results, transcript_results, intertextual_results = await asyncio.gather(
        asyncio.gather(*video_tasks),
        asyncio.gather(*transcript_tasks),
        asyncio.gather(*intertextual_tasks),
    )

    # Save interim work products
    save_tasks = []
    for i, (video_analysis, transcript_analysis, intertextual_analysis) in enumerate(
        zip(video_results, transcript_results, intertextual_results)
    ):
        chunk_start, chunk_end = chunk_infos[i]
        save_tasks.extend(
            [
                save_interim_work_product(
                    video_analysis,
                    video_id,
                    video_title,
                    f"video_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
                ),
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
            ]
        )

    await asyncio.gather(*save_tasks)

    # Consolidate results
    consolidation_tasks = [
        consolidate_analyses(video_results, video_id, video_title, "video"),
        consolidate_analyses(transcript_results, video_id, video_title, "transcript"),
        consolidate_analyses(
            intertextual_results, video_id, video_title, "intertextual"
        ),
    ]
    (
        consolidated_video,
        consolidated_transcript,
        consolidated_intertextual,
    ) = await asyncio.gather(*consolidation_tasks)

    end_time = time.time()
    await api_stats.record_process("process_video", start_time, end_time)

    logger.info("Video processing complete")
    return consolidated_intertextual, consolidated_video, consolidated_transcript


async def consolidate_analyses(
    analyses: List[str], video_id: str, video_title: str, analysis_type: str
) -> str:
    consolidated = "\n\n".join(analyses)

    if analysis_type == "intertextual":
        prompt = f"""
        Combine the following JSON analyses into a single coherent JSON document:

        {consolidated}

        Instructions:
        1. Be aware that each chunk may have a different JSON structure or schema.
        2. Create a unified structure that accommodates all unique keys and data types from the input chunks.
        3. Maintain the original JSON structure of individual entries as much as possible.
        4. Combine similar entries, removing exact duplicates, but preserve unique information even if keys differ.
        5. If entries have common keys (e.g., "type", "reference", "context"), use these as a basis for organization.
        6. For entries with unique keys, include them in the consolidated structure, grouping similar concepts where possible.
        7. Preserve the chronological order of entries if applicable.
        8. Do not alter the content of individual entries beyond removing exact duplicates.
        9. If there are conflicting data types for the same key, use a structure that can accommodate both (e.g., an array of possible types).

        Format the output as a valid JSON document that encompasses all unique data from the input chunks.
        """
    else:
        prompt = f"""
        Combine the following {analysis_type} analyses into a single coherent document:

        {consolidated}

        Instructions:
        1. Maintain the original structure and content of each chunk.
        2. Combine the chunks in chronological order.
        3. Use appropriate Markdown formatting to clearly delineate between chunks.
        4. Retain all original headings, subheadings, and content organization.
        5. Do not summarize or alter the content in any way.
        6. Ensure that all information from each chunk is preserved in its entirety.
        7. Use clear section breaks (e.g., horizontal rules) to separate chunks if necessary.

        The output should be a well-formatted Markdown document that includes all original content from the input chunks, preserving their structure and detail.
        """

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
