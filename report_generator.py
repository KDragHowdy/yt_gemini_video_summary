import os


def generate_markdown_report(video_id, video_title, chunks):
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


def generate_and_save_reports(video_id, video_title, summary_chunks, output_dir):
    report = generate_markdown_report(video_id, video_title, summary_chunks)

    # Save report
    report_file = os.path.join(output_dir, f"{video_id}_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to {report_file}")
