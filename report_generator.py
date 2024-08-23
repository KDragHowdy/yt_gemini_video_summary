import os
import json
from datetime import datetime
from content_generator import generate_content


def generate_markdown_report(
    video_id, video_title, summary_chunks, intertextual_references
):
    combined_summary = "\n\n".join(summary_chunks)

    prompt = f"""
    Organize and synthesize the following summary chunks into a coherent final report for the video "{video_title}" (ID: {video_id}):

    {combined_summary}

    Please structure the report with the following sections:
    1. Executive Summary
    2. Key Points and Insights
    3. Chronological Overview
    4. Visual Elements and Their Significance
    5. Intertextual References and Their Context
    6. Conclusion and Future Implications

    Use appropriate Markdown formatting for headings and subheadings.
    """

    organized_report = generate_content(prompt)

    markdown_content = f"""
# Video Analysis Report: {video_title}

Video ID: {video_id}

{organized_report}

## Intertextual References

"""

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


def generate_structured_slides_appendix(video_id, video_title):
    interim_dir = "./interim"
    markdown_content = "# Appendix A: Structured Slides\n\n"

    video_analysis_files = [
        f
        for f in os.listdir(interim_dir)
        if f.startswith(f"wp_{video_id}_video_analysis_chunk_")
    ]
    video_analysis_files.sort()

    for file in video_analysis_files:
        with open(os.path.join(interim_dir, file), "r", encoding="utf-8") as f:
            content = f.read()
        chunk_info = file.split("_chunk_")[1].split(".")[0]
        markdown_content += f"## Chunk {chunk_info}\n\n{content}\n\n"

    return markdown_content


def generate_and_save_reports(
    video_id, video_title, summary_chunks, intertextual_references, output_dir
):
    try:
        main_report = generate_markdown_report(
            video_id, video_title, summary_chunks, intertextual_references
        )
        structured_slides = generate_structured_slides_appendix(video_id, video_title)

        full_report = f"{main_report}\n\n{structured_slides}\n\n# Appendix B: Intertextual Analysis\n\n{json.dumps(intertextual_references, indent=2)}"

        # Create shortened title
        shortened_title = "".join(e for e in video_title if e.isalnum())[:20].lower()

        # Generate filename
        filename = f"final_report_{shortened_title}.md"

        # Save report
        report_file = os.path.join(output_dir, filename)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(full_report)

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
