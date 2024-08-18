import os


def generate_markdown_report(video_id, video_title, chunks, intertextual_references):
    markdown_content = f"""
# Video Analysis Report: {video_title}

Video ID: {video_id}

"""

    for i, chunk in enumerate(chunks, 1):
        markdown_content += f"""
## Segment {i}

{chunk}

"""

    markdown_content += "\n## Intertextual References\n\n"
    for ref in intertextual_references:
        markdown_content += f"""
### {ref['type'].capitalize()} Reference: {ref['reference']}
- Context: {ref['context']}
- Explanation: {ref['explanation']}
- Significance: {ref['significance']}

"""

    return markdown_content


def generate_and_save_reports(
    video_id, video_title, summary_chunks, intertextual_references, output_dir
):
    report = generate_markdown_report(
        video_id, video_title, summary_chunks, intertextual_references
    )

    # Create shortened title
    shortened_title = "".join(e for e in video_title if e.isalnum())[:20].lower()

    # Generate filename
    filename = f"final_report_{shortened_title}.md"

    # Save report
    report_file = os.path.join(output_dir, filename)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Final report saved to {report_file}")
    return report_file
