# video_processor.py

import asyncio
import time
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


async def rate_limited_api_call(func, *args, **kwargs):
    await api_stats.wait_for_rate_limit()
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        current_time = time.time()
        time_elapsed = current_time - api_stats.minute_start
        debug_print(
            f"Error occurred. Current counter: {api_stats.call_counter}, Time elapsed: {time_elapsed:.2f}s"
        )
        if "429" in str(e):
            debug_print("Received 429 error. Retrying once...")
            await asyncio.sleep(1)
            await api_stats.wait_for_rate_limit()
            return await func(*args, **kwargs)
        raise


async def process_video(
    video_chunks: List[str],
    video_id: str,
    video_title: str,
    duration_minutes: float,
    transcript: str,
) -> Tuple[str, str, str]:
    start_time = time.time()
    debug_print("Starting video processing")

    # Upload all video chunks at the beginning
    upload_tasks = [upload_video(chunk_path) for chunk_path in video_chunks]
    uploaded_files = await asyncio.gather(*upload_tasks)
    debug_print("All video chunks uploaded")

    async def process_chunk(
        chunk_path: str,
        chunk_start: float,
        chunk_end: float,
        chunk_transcript: str,
        video_file,
    ):
        debug_print(f"Processing chunk {chunk_start}-{chunk_end}")

        try:
            # Perform transcript and intertextual analyses immediately
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

            debug_print(f"Chunk {chunk_start}-{chunk_end} processing complete")
            return video_analysis, transcript_analysis, intertextual_analysis
        except Exception as e:
            debug_print(f"Error processing chunk {chunk_start}-{chunk_end}: {str(e)}")
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
    await api_stats.record_process("process_video", start_time, end_time)

    debug_print("Video processing complete")
    return consolidated_intertextual, consolidated_video, consolidated_transcript


async def consolidate_analyses(
    analyses: List[str], video_id: str, video_title: str, analysis_type: str
) -> str:
    consolidated = "\n\n".join(analyses)
    prompt = f"Consolidate and summarize the following {analysis_type} analyses:\n\n{consolidated}"

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
