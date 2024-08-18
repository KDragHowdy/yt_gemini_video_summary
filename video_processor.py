from file_uploader import upload_video, wait_for_file_active
from content_generator import (
    analyze_combined_video_and_transcript_wp,
    analyze_video_content,
    analyze_transcript,
    save_interim_work_product,
)
from utils import get_transcript, consolidate_work_products
from error_handling import handle_exceptions, VideoProcessingError
from prompt_logic_intertextual import analyze_intertextual_references
import time


@handle_exceptions
def process_video(video_chunks, video_id, video_title, duration_minutes):
    transcript = get_transcript(video_id)
    if not transcript:
        raise VideoProcessingError("Unable to retrieve transcript")

    print(f"Successfully retrieved transcript ({len(transcript)} characters).")

    summary_chunks = []
    intertextual_chunks = []

    for i, chunk_path in enumerate(video_chunks):
        chunk_start = i * 20  # Assuming 20-minute chunks
        chunk_end = min((i + 1) * 20, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]

        print(f"Processing chunk {chunk_start}-{chunk_end} minutes...")

        # Upload and process video chunk
        video_file = upload_video(chunk_path)
        video_file = wait_for_file_active(video_file)

        # Analyze video content
        video_analysis = analyze_video_content(video_file, chunk_start, chunk_end)
        save_interim_work_product(
            video_analysis,
            video_id,
            video_title,
            f"video_analysis_chunk_{chunk_start}_{chunk_end}",
        )

        # Analyze transcript
        transcript_analysis = analyze_transcript(
            chunk_transcript, chunk_start, chunk_end
        )
        save_interim_work_product(
            transcript_analysis,
            video_id,
            video_title,
            f"transcript_analysis_chunk_{chunk_start}_{chunk_end}",
        )

        # Perform intertextual analysis
        intertextual_analysis = analyze_intertextual_references(
            video_analysis, transcript_analysis, chunk_start, chunk_end
        )
        save_interim_work_product(
            intertextual_analysis,
            video_id,
            video_title,
            f"intertextual_analysis_chunk_{chunk_start}_{chunk_end}",
        )

        # Generate combined summary
        summary = analyze_combined_video_and_transcript_wp(
            video_analysis,
            transcript_analysis,
            intertextual_analysis,
            chunk_start,
            chunk_end,
            video_id,
            video_title,
        )
        summary_chunks.append(summary)
        save_interim_work_product(
            summary,
            video_id,
            video_title,
            f"summary_chunk_{chunk_start}_{chunk_end}",
        )

        intertextual_chunks.append(intertextual_analysis)

        time.sleep(4)  # To respect the rate limit of 15 RPM

    # Consolidate work products
    print("Debug: Starting consolidation of work products")
    for analysis_type in [
        "video_analysis",
        "transcript_analysis",
        "intertextual_analysis",
    ]:
        print(f"Debug: Consolidating {analysis_type}")
        consolidated_content = consolidate_work_products(
            video_id, video_title, analysis_type
        )
        print(
            f"Debug: Consolidated {analysis_type} content length: {len(consolidated_content)}"
        )

    return summary_chunks, intertextual_chunks
