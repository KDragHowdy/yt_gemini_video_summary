from file_uploader import upload_video, wait_for_file_active
from content_generator import process_video_chunk, process_video_chunk_second_draft
from utils import get_transcript
import time


def process_video(video_path, video_id, duration_minutes):
    video_file = upload_video(video_path)
    video_file = wait_for_file_active(video_file)

    transcript = get_transcript(video_id)
    if not transcript:
        print("Error: Unable to retrieve transcript. Exiting.")
        return [], []

    print(f"Successfully retrieved transcript ({len(transcript)} characters).")

    first_draft_chunks = []
    second_draft_chunks = []
    for i in range(0, int(duration_minutes), 60):
        chunk_start = i
        chunk_end = min(i + 60, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]  # Assuming 10 words per second

        print(f"Processing chunk {chunk_start}-{chunk_end} minutes...")
        first_draft = process_video_chunk(
            video_file, chunk_transcript, chunk_start, chunk_end
        )
        first_draft_chunks.append(first_draft)

        if "Error in analysis" in first_draft:
            print(
                f"Skipping second draft for chunk {chunk_start}-{chunk_end} due to error in first draft."
            )
            second_draft_chunks.append(first_draft)
        else:
            print(
                f"Generating second draft for chunk {chunk_start}-{chunk_end} minutes..."
            )
            second_draft = process_video_chunk_second_draft(first_draft)
            second_draft_chunks.append(second_draft)

        time.sleep(4)  # To respect the rate limit of 15 RPM

    return first_draft_chunks, second_draft_chunks
