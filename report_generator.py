import json
from models import get_gemini_pro_model


def extract_visual_elements(video_analyses):
    visual_elements_summary = []
    for analysis in video_analyses:
        try:
            structured_elements = json.loads(analysis).get("structured_elements", [])
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


def format_intertextual_references(intertextual_chunks):
    formatted_references = []
    for chunk in intertextual_chunks:
        try:
            chunk_data = json.loads(chunk)
            for ref in chunk_data.get("references", []):
                formatted_references.append(
                    f"- {ref.get('type', 'Unknown').capitalize()} Reference: {ref.get('reference', 'N/A')}\n"
                    f"  Context: {ref.get('context', 'N/A')}\n"
                    f"  Significance: {ref.get('significance', 'N/A')}\n"
                )
        except json.JSONDecodeError:
            print(f"Error parsing intertextual chunk: {chunk[:100]}...")
    return "\n".join(formatted_references)


def generate_markdown_report(
    video_id, video_title, summary_chunks, intertextual_chunks, video_analyses
):
    combined_summary = "\n\n".join(summary_chunks)
    visual_elements = extract_visual_elements(video_analyses)
    formatted_intertextual = format_intertextual_references(intertextual_chunks)

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
    - Format the output as a properly structured Markdown document, not as JSON.
    """

    model = get_gemini_pro_model()
    response = model.generate_content(prompt)

    try:
        report_data = json.loads(response.text)
        markdown_report = f"""
# {video_title} - AI Predictions Analysis

## 1. Executive Summary

{report_data.get('Executive Summary', 'No executive summary provided.')}

## 2. Detailed Analysis

### Key Points and Insights

{report_data.get('Detailed Analysis', {}).get('Key Points and Insights', 'No key points provided.')}

### Chronological Overview

{report_data.get('Detailed Analysis', {}).get('Chronological Overview', 'No chronological overview provided.')}

## 3. Implications and Future Outlook

{report_data.get('Implications and Future Outlook', 'No implications and future outlook provided.')}
        """
    except json.JSONDecodeError:
        # If it's not JSON, assume it's already in markdown format
        markdown_report = response.text

    return markdown_report


def generate_structured_slides_appendix(video_id, video_title, video_analyses):
    markdown_content = "# Appendix A: Structured Slides\n\n"
    slide_number = 1

    for analysis in video_analyses:
        try:
            structured_elements = json.loads(analysis).get("structured_elements", [])
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
