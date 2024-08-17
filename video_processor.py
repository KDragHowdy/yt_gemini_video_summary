from file_uploader import upload_video, wait_for_file_active
from content_generator import analyze_combined_video_and_transcript_wp
from utils import get_transcript
from error_handling import handle_exceptions, VideoProcessingError
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

    for i in range(0, int(duration_minutes), 60):
        chunk_start = i
        chunk_end = min(i + 60, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]

        print(f"Processing chunk {chunk_start}-{chunk_end} minutes...")

        summary = analyze_combined_video_and_transcript_wp(
            video_file, chunk_transcript, chunk_start, chunk_end, video_id, video_title
        )
        summary_chunks.append(summary)

        time.sleep(4)  # To respect the rate limit of 15 RPM

    return summary_chunks
