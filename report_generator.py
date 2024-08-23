import os
import json
from models import get_gemini_pro_model


def extract_visual_elements(video_analyses):
    visual_elements_summary = []
    for analysis in video_analyses:
        try:
            structured_elements = json.loads(analysis)["structured_elements"]
            for element in structured_elements:
                if element.get("element_type") == "slide":
                    content = element.get("content", "")
                    if isinstance(content, str):
                        title = content.split("\n")[0] if "\n" in content else content
                        body = (
                            "\n".join(content.split("\n")[1:])
                            if "\n" in content
                            else ""
                        )
                    elif isinstance(content, dict):
                        title = content.get("title", "No title")
                        body = content.get("text", "")
                    else:
                        title = "Unknown format"
                        body = str(content)
                    visual_elements_summary.append(f"- {title}\n  {body}")
        except json.JSONDecodeError:
            print(f"Error parsing JSON in video analysis. Skipping this chunk.")
            continue
        except KeyError as e:
            print(f"KeyError in video analysis: {str(e)}. Skipping this element.")
            continue
        except Exception as e:
            print(f"Unexpected error in extract_visual_elements: {str(e)}")
            continue
    return "\n\n".join(visual_elements_summary)


def format_intertextual_references(intertextual_references):
    formatted_references = []
    if (
        isinstance(intertextual_references, dict)
        and "references" in intertextual_references
    ):
        for ref in intertextual_references["references"]:
            formatted_references.append(
                f"- {ref.get('type', 'Unknown').capitalize()} Reference: {ref.get('reference', 'N/A')}\n  Context: {ref.get('context', 'N/A')}\n  Significance: {ref.get('significance', 'N/A')}"
            )
    return "\n\n".join(formatted_references)


def generate_markdown_report(
    video_id, video_title, summary_chunks, intertextual_references, video_analyses
):
    combined_summary = "\n\n".join(summary_chunks)

    visual_elements = extract_visual_elements(video_analyses)
    formatted_intertextual = format_intertextual_references(intertextual_references)

    prompt = f"""
    Organize and synthesize the following information into a coherent final report for the video "{video_title}" (ID: {video_id}):

    Summary:
    {combined_summary}

    Visual Elements:
    {visual_elements}

    Intertextual References:
    {formatted_intertextual}

    Please structure the report with the following sections:
    1. Executive Summary
    2. Detailed Analysis
       - Key Points and Insights
       - Chronological Overview (incorporate visual elements and intertextual references where relevant)
    3. Implications and Future Outlook

    Guidelines:
    - Integrate visual elements and intertextual references throughout the analysis where they provide context or deeper understanding.
    - Use the intertextual references to explain complex concepts or cultural references mentioned in the video.
    - Ensure smooth transitions between different parts of the video and provide concluding remarks.
    - Format the output as a valid JSON object with keys corresponding to each section.
    """

    model = get_gemini_pro_model()
    response = model.generate_content(prompt)

    try:
        report_data = json.loads(response.text)
    except json.JSONDecodeError:
        print("Error: Unable to parse JSON response. Falling back to raw text.")
        return response.text

    markdown_report = f"""
# {video_title} - AI Predictions Analysis

## 1. Executive Summary

{report_data.get('executive_summary', 'No executive summary provided.')}

## 2. Detailed Analysis

### Key Points and Insights

{report_data.get('key_points_and_insights', 'No key points provided.')}

### Chronological Overview

{report_data.get('chronological_overview', 'No chronological overview provided.')}

## 3. Implications and Future Outlook

{report_data.get('implications_and_future_outlook', 'No implications and future outlook provided.')}
    """

    return markdown_report


def generate_structured_slides_appendix(video_id, video_title, video_analyses):
    markdown_content = "# Appendix A: Structured Slides\n\n"
    slide_number = 1

    for analysis in video_analyses:
        try:
            structured_elements = json.loads(analysis)["structured_elements"]
            for element in structured_elements:
                if element.get("element_type") == "slide":
                    content = element.get("content", "")
                    if isinstance(content, str):
                        title = content.split("\n")[0] if "\n" in content else content
                        body = (
                            "\n".join(content.split("\n")[1:])
                            if "\n" in content
                            else ""
                        )
                    elif isinstance(content, dict):
                        title = content.get("title", "No title")
                        body = content.get("text", "")
                    else:
                        title = "Unknown format"
                        body = str(content)
                    markdown_content += (
                        f"## Slide {slide_number}: {title}\n\n{body}\n\n"
                    )
                    slide_number += 1
        except json.JSONDecodeError:
            print(f"Error parsing JSON in video analysis. Skipping this chunk.")
            continue
        except KeyError as e:
            print(f"KeyError in video analysis: {str(e)}. Skipping this element.")
            continue
        except Exception as e:
            print(f"Unexpected error in extract_visual_elements: {str(e)}")
            continue

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
            video_id,
            video_title,
            summary_chunks,
            intertextual_references,
            video_analyses,
        )
        structured_slides = generate_structured_slides_appendix(
            video_id, video_title, video_analyses
        )

        # Create shortened title
        shortened_title = "".join(e for e in video_title if e.isalnum())[:20].lower()

        # Generate filename
        filename = f"final_report_{shortened_title}.md"

        # Combine main report and appendices
        full_report = f"{main_report}\n\n{structured_slides}\n\n"

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

        # Print more detailed information about video_analyses
        print("Debug: video_analyses content:")
        for i, analysis in enumerate(video_analyses):
            print(f"Analysis {i}:")
            print(analysis[:500])  # Print first 500 characters of each analysis

        raise  # Re-raise the exception after logging debug info
