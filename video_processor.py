# video_processor.py

import time
from file_uploader import upload_video, wait_for_file_active
from content_generator import (
    analyze_video_content,
    analyze_transcript,
    save_interim_work_product,
)
from utils import get_transcript
from error_handling import handle_exceptions, VideoProcessingError
from prompt_logic_intertextual import analyze_intertextual_references
from api_statistics import api_stats
import asyncio


@handle_exceptions
async def process_video(video_chunks, video_id, video_title, duration_minutes):
    start_time = time.time()
    transcript = await get_transcript(video_id)
    if not transcript:
        raise VideoProcessingError("Unable to retrieve transcript")

    print(f"Successfully retrieved transcript ({len(transcript)} characters).")

    chunk_tasks = []
    for i, chunk_path in enumerate(video_chunks):
        chunk_start = i * 10
        chunk_end = min((i + 1) * 10, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]

        task = asyncio.create_task(
            process_chunk(
                chunk_path,
                video_id,
                video_title,
                chunk_transcript,
                chunk_start,
                chunk_end,
            )
        )
        chunk_tasks.append(task)

    results = await asyncio.gather(*chunk_tasks)

    intertextual_chunks = []
    video_analyses = []
    for intertextual_analysis, video_analysis in results:
        if intertextual_analysis:
            intertextual_chunks.append(intertextual_analysis)
        if video_analysis:
            video_analyses.append(video_analysis)

    end_time = time.time()
    await api_stats.record_process("process_video", start_time, end_time)
    return intertextual_chunks, video_analyses


async def process_chunk(
    chunk_path, video_id, video_title, chunk_transcript, chunk_start, chunk_end
):
    chunk_start_time = time.time()
    try:
        print(f"Processing chunk {chunk_start:03.0f}-{chunk_end:03.0f} minutes...")

        # Upload and process video chunk
        upload_start = time.time()
        video_file = await upload_video(chunk_path)
        upload_end = time.time()
        await api_stats.record_process(
            f"upload_video_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
            upload_start,
            upload_end,
        )

        wait_start = time.time()
        video_file = await wait_for_file_active(video_file)
        wait_end = time.time()
        await api_stats.record_process(
            f"wait_for_file_active_{chunk_start:03.0f}_{chunk_end:03.0f}",
            wait_start,
            wait_end,
        )

        # Analyze video content
        video_analysis_start = time.time()
        video_analysis = await analyze_video_content(video_file, chunk_start, chunk_end)
        video_analysis_end = time.time()
        await api_stats.record_process(
            f"analyze_video_content_{chunk_start:03.0f}_{chunk_end:03.0f}",
            video_analysis_start,
            video_analysis_end,
        )

        await save_interim_work_product(
            video_analysis,
            video_id,
            video_title,
            f"video_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
        )

        # Analyze transcript
        transcript_analysis_start = time.time()
        transcript_analysis = await analyze_transcript(
            chunk_transcript, chunk_start, chunk_end
        )
        transcript_analysis_end = time.time()
        await api_stats.record_process(
            f"analyze_transcript_{chunk_start:03.0f}_{chunk_end:03.0f}",
            transcript_analysis_start,
            transcript_analysis_end,
        )

        await save_interim_work_product(
            transcript_analysis,
            video_id,
            video_title,
            f"transcript_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
        )

        # Perform intertextual analysis
        intertextual_analysis_start = time.time()
        intertextual_analysis = await analyze_intertextual_references(
            video_analysis, transcript_analysis, chunk_start, chunk_end
        )
        intertextual_analysis_end = time.time()
        await api_stats.record_process(
            f"analyze_intertextual_references_{chunk_start:03.0f}_{chunk_end:03.0f}",
            intertextual_analysis_start,
            intertextual_analysis_end,
        )

        await save_interim_work_product(
            intertextual_analysis,
            video_id,
            video_title,
            f"intertextual_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
        )

        return intertextual_analysis, video_analysis

    except Exception as e:
        print(f"Error processing chunk {chunk_start:03.0f}-{chunk_end:03.0f}: {str(e)}")
        error_content = (
            f"Error in chunk {chunk_start:03.0f}-{chunk_end:03.0f}: {str(e)}"
        )
        await save_interim_work_product(
            error_content,
            video_id,
            video_title,
            f"error_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
        )
        return None, None

    finally:
        chunk_end_time = time.time()
        await api_stats.record_process(
            f"process_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
            chunk_start_time,
            chunk_end_time,
        )
        await asyncio.sleep(
            2
        )  # Reduced from 4 to 2 seconds to account for more frequent, smaller chunks
