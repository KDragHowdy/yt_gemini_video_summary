import os
import json


def generate_markdown_report(video_id, video_title, chunks, intertextual_references):
    print(
        f"Debug: Type of intertextual_references in generate_markdown_report: {type(intertextual_references)}"
    )
    print(
        f"Debug: Content of intertextual_references in generate_markdown_report: {intertextual_references}"
    )

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

    if (
        isinstance(intertextual_references, dict)
        and "references" in intertextual_references
    ):
        references = intertextual_references["references"]
        if references:
            for ref in references:
                markdown_content += f"""
### {ref.get('type', 'Unknown').capitalize()} Reference: {ref.get('reference', 'N/A')}
- Context: {ref.get('context', 'N/A')}
- Explanation: {ref.get('explanation', 'N/A')}
- Significance: {ref.get('significance', 'N/A')}

"""
        else:
            markdown_content += "No intertextual references found.\n"
    else:
        markdown_content += (
            "Error: Intertextual references data is not in the expected format.\n"
        )

    return markdown_content


def generate_and_save_reports(
    video_id, video_title, summary_chunks, intertextual_references, output_dir
):
    try:
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
    except Exception as e:
        print(f"Error in generate_and_save_reports: {str(e)}")
        print(f"Debug: video_id = {video_id}")
        print(f"Debug: video_title = {video_title}")
        print(f"Debug: summary_chunks type = {type(summary_chunks)}")
        print(f"Debug: intertextual_references type = {type(intertextual_references)}")
        print(f"Debug: output_dir = {output_dir}")
        raise  # Re-raise the exception after logging debug info
