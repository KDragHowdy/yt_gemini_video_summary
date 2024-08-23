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
    5. Conclusion and Future Implications

    Use appropriate Markdown formatting for headings and subheadings. Ensure smooth transitions between different parts of the video and provide concluding remarks.
    """

    organized_report = generate_content(prompt)

    return organized_report


def generate_structured_slides_appendix(video_id, video_title, video_analyses):
    markdown_content = "# Appendix A: Structured Slides\n\n"

    for i, analysis in enumerate(video_analyses, 1):
        markdown_content += f"## Chunk {i}\n\n{analysis}\n\n"

    return markdown_content


def generate_and_save_reports(
    video_id,
    video_title,
    summary_chunks,
    intertextual_references,
    video_analyses,
    output_dir,
):
    try:
        main_report = generate_markdown_report(
            video_id, video_title, summary_chunks, intertextual_references
        )

        try:
            structured_slides = generate_structured_slides_appendix(
                video_id, video_title, video_analyses
            )
        except Exception as e:
            print(f"Error generating structured slides appendix: {str(e)}")
            structured_slides = "# Appendix A: Structured Slides\n\nError generating structured slides appendix."

        # Format intertextual references
        intertextual_content = "# Appendix B: Intertextual Analysis\n\n"
        if (
            isinstance(intertextual_references, dict)
            and "references" in intertextual_references
        ):
            for ref in intertextual_references["references"]:
                intertextual_content += f"""
## {ref.get('type', 'Unknown').capitalize()} Reference: {ref.get('reference', 'N/A')}
- **Context:** {ref.get('context', 'N/A')}
- **Explanation:** {ref.get('explanation', 'N/A')}
- **Significance:** {ref.get('significance', 'N/A')}

"""
        else:
            intertextual_content += (
                "Error: Intertextual references data is not in the expected format.\n"
            )

        full_report = f"{main_report}\n\n{structured_slides}\n\n{intertextual_content}"

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
        print(f"Debug: video_analyses type = {type(video_analyses)}")
        print(f"Debug: output_dir = {output_dir}")
        raise  # Re-raise the exception after logging debug info
