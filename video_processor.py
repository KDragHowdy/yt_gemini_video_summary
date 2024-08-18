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
def process_video(video_path, video_id, video_title, duration_minutes):
    video_file = upload_video(video_path)
    video_file = wait_for_file_active(video_file)

    transcript = get_transcript(video_id)
    if not transcript:
        raise VideoProcessingError("Unable to retrieve transcript")

    print(f"Successfully retrieved transcript ({len(transcript)} characters).")

    summary_chunks = []
    intertextual_chunks = []

    for i in range(0, int(duration_minutes), 15):
        chunk_start = i
        chunk_end = min(i + 15, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]

        print(f"Processing chunk {chunk_start}-{chunk_end} minutes...")

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
    consolidate_work_products(video_id, video_title, "video_analysis")
    consolidate_work_products(video_id, video_title, "transcript_analysis")
    consolidate_work_products(video_id, video_title, "intertextual_analysis")
    consolidate_work_products(video_id, video_title, "summary")

    return summary_chunks, intertextual_chunks
