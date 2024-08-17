import os


def generate_markdown_report(video_id, video_title, chunks, draft_number):
    markdown_content = f"""
# Video Analysis Report: {video_title}

Video ID: {video_id}

"""

    for i, chunk in enumerate(chunks, 1):
        markdown_content += f"""
## Segment {i}

{chunk}

"""

    return markdown_content


def generate_and_save_reports(
    video_id, video_title, first_draft_chunks, second_draft_chunks, output_dir
):
    first_draft_report = generate_markdown_report(
        video_id, video_title, first_draft_chunks, 1
    )
    second_draft_report = generate_markdown_report(
        video_id, video_title, second_draft_chunks, 2
    )

    # Save first draft
    first_draft_file = os.path.join(output_dir, f"{video_id}_report_draft1.md")
    with open(first_draft_file, "w", encoding="utf-8") as f:
        f.write(first_draft_report)

    # Save second draft
    second_draft_file = os.path.join(output_dir, f"{video_id}_report_draft2.md")
    with open(second_draft_file, "w", encoding="utf-8") as f:
        f.write(second_draft_report)

    print(f"First draft report saved to {first_draft_file}")
    print(f"Second draft report saved to {second_draft_file}")
