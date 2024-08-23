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
    video_analyses = []

    for i, chunk_path in enumerate(video_chunks):
        try:
            chunk_start = i * 10
            chunk_end = min((i + 1) * 10, duration_minutes)
            chunk_transcript = transcript[
                int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
            ]

            print(f"Processing chunk {chunk_start:03.0f}-{chunk_end:03.0f} minutes...")

            # Upload and process video chunk
            video_file = upload_video(chunk_path)
            video_file = wait_for_file_active(video_file)

            # Analyze video content
            video_analysis = analyze_video_content(video_file, chunk_start, chunk_end)
            save_interim_work_product(
                video_analysis,
                video_id,
                video_title,
                f"video_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
            )
            video_analyses.append(video_analysis)

            # Analyze transcript
            transcript_analysis = analyze_transcript(
                chunk_transcript, chunk_start, chunk_end
            )
            save_interim_work_product(
                transcript_analysis,
                video_id,
                video_title,
                f"transcript_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
            )

            # Perform intertextual analysis
            intertextual_analysis = analyze_intertextual_references(
                video_analysis, transcript_analysis, chunk_start, chunk_end
            )
            save_interim_work_product(
                intertextual_analysis,
                video_id,
                video_title,
                f"intertextual_analysis_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
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
                f"summary_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
            )

            intertextual_chunks.append(intertextual_analysis)

        except Exception as e:
            print(f"Error processing chunk {i+1}: {str(e)}")
            error_content = f"Error in chunk {i+1}: {str(e)}"
            save_interim_work_product(
                error_content,
                video_id,
                video_title,
                f"error_chunk_{chunk_start:03.0f}_{chunk_end:03.0f}",
            )
            continue  # Move to the next chunk

        time.sleep(
            2
        )  # Reduced from 4 to 2 seconds to account for more frequent, smaller chunks

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

    return summary_chunks, intertextual_chunks, video_analyses
