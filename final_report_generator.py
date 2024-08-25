import os
import json
from typing import List, Dict
from models import get_gemini_flash_model_text, get_gemini_flash_model_json

BASE_DIR = r"C:\\Users\\kevin\\repos\\yt_gemini_video_summary"
INTERIM_DIR = os.path.join(BASE_DIR, "interim")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def load_work_products(interim_dir: str) -> Dict[str, List[str]]:
    work_products = {
        "video_analysis": [],
        "transcript_analysis": [],
        "intertextual_analysis": [],
    }

    print(f"Debug: Searching for files in {interim_dir}")
    for filename in os.listdir(interim_dir):
        print(f"Debug: Found file: {filename}")
        if filename.endswith(".txt"):
            file_path = os.path.join(interim_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        print(f"Warning: File {filename} is empty.")
                        continue

                    if "video_chunk" in filename:
                        work_products["video_analysis"].append(content)
                        print(
                            f"Debug: Loaded video_analysis from {filename} (length: {len(content)})"
                        )
                    elif "transcript_chunk" in filename:
                        work_products["transcript_analysis"].append(content)
                        print(
                            f"Debug: Loaded transcript_analysis from {filename} (length: {len(content)})"
                        )
                    elif "intertextual_chunk" in filename:
                        work_products["intertextual_analysis"].append(content)
                        print(
                            f"Debug: Loaded intertextual_analysis from {filename} (length: {len(content)})"
                        )
                    else:
                        print(
                            f"Debug: Skipping file {filename} as it doesn't match any known type."
                        )
            except IOError as e:
                print(f"Error reading file {filename}: {str(e)}")
            except Exception as e:
                print(f"Unexpected error processing file {filename}: {str(e)}")

    for wp_type, chunks in work_products.items():
        print(f"Debug: Total {wp_type} chunks loaded: {len(chunks)}")

    return work_products


def save_prompt(prompt: str, filename: str):
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"Debug: Saved prompt to {filename}")


def consolidate_chunks(chunks: List[str], work_product_type: str) -> str:
    print(f"Debug: Consolidating {work_product_type} chunks (total: {len(chunks)})")

    if work_product_type == "intertextual_analysis":
        model = get_gemini_flash_model_json()
    else:
        model = get_gemini_flash_model_text()

    chunks_text = "\n\n".join(chunks)
    prompt = (
        f"Consolidate the following {work_product_type} chunks into a single coherent document:\n\n"
        f"{chunks_text}\n\n"
        "Instructions:\n"
        "1. Identify the common headers across all chunks.\n"
        "2. For each header, combine the relevant content from all chunks, maintaining the original sequence.\n"
        "3. Present the consolidated information under a single set of headers.\n"
        "4. Ensure all unique information from each chunk is retained.\n"
        "5. Maintain the chronological order of information where applicable.\n"
        "6. Do not summarize or paraphrase the content; instead, reorganize it.\n\n"
        "Format the output as a well-structured Markdown document."
    )

    save_prompt(prompt, f"prompt_consolidate_{work_product_type}.txt")

    response = model.generate_content(prompt)
    consolidated = response.text
    print(f"Debug: Consolidated {work_product_type} length: {len(consolidated)}")

    output_file = os.path.join(OUTPUT_DIR, f"consolidated_{work_product_type}.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(consolidated)
    print(f"Debug: Saved consolidated {work_product_type} to {output_file}")

    return consolidated


def generate_integrated_report(
    consolidated_products: Dict[str, str],
    video_title: str,
    video_date: str,
    channel_name: str,
    speaker_name: str,
) -> str:
    model = get_gemini_flash_model_text()
    # Create the report title
    report_title = f"Understanding the Implications of AI: A Holistic Examination\n{video_title} ({video_date}) - {channel_name} by {speaker_name}"

    # Create the prompt
    prompt = f"""
    Title: {report_title}

    Write a comprehensive report on the topic discussed in the video, using the provided analyses as a knowledge base. The report should:
    - Maintain a formal structure with sections and headings while allowing for the expressive style of an essay where necessary.
    - Integrate facts, quotes, and key arguments from the transcript analysis into a cohesive narrative that reflects a deep understanding of the topic.
    - Incorporate insights from the video analysis (slides, graphs, etc.) into the report, using them to enrich the discussion while keeping the detailed slides and structured elements in the appendix.
    - Use context from the intertextual analysis to clarify references, jargon, or concepts that the speaker assumes the audience understands, helping to explain these elements within the report.
    - Reference quotes and facts from the video directly within the text, using them to add depth and credibility to the analysis, ensuring they feel naturally embedded in the narrative.
    - Ensure the report flows logically, capturing the progression of ideas without resorting to a simple chronological retelling. Instead, focus on how the speaker’s arguments build upon each other, structured thematically or by major argument points.
    - Avoid empty summarization or disconnected recounting of events. The report should present a concentrated, analytical discussion that conveys expertise and insight, using the provided materials to inform a nuanced exploration of the topic.

    The report should be formatted in Markdown with appropriate sections and headings, ensuring that the narrative is clear, authoritative, and compelling.
    """

    save_prompt(prompt, "prompt_integrated_report.txt")

    response = model.generate_content(prompt)
    integrated_report = response.text
    print(f"Generated integrated report length: {len(integrated_report)}")

    output_file = os.path.join(OUTPUT_DIR, "integrated_report.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(integrated_report)
    print(f"Saved integrated report to {output_file}")

    return integrated_report


def generate_structured_elements_appendix(video_analysis: str) -> str:
    print("Debug: Generating structured elements appendix")
    model = get_gemini_flash_model_text()
    prompt = f"""
    Generate an appendix of structured elements based on the following video analysis:

    {video_analysis}

    Please structure the appendix with the following sections:
    1. Slides
    2. Graphs and Charts
    3. Code Snippets
    4. Other Structured Elements

    For each structured element, include the timestamp, a brief description, and any relevant details.

    Use Markdown formatting for better readability.
    """

    save_prompt(prompt, "prompt_structured_elements_appendix.txt")

    response = model.generate_content(prompt)
    appendix = response.text
    print(f"Generated structured elements appendix length: {len(appendix)}")

    output_file = os.path.join(OUTPUT_DIR, "structured_elements_appendix.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(appendix)
    print(f"Saved structured elements appendix to {output_file}")

    return appendix


def generate_intertextual_analysis_appendix(intertextual_analysis: str) -> str:
    print("Debug: Generating intertextual analysis appendix")
    model = get_gemini_flash_model_text()
    prompt = f"""
    Generate an appendix for intertextual analysis based on the following content:

    {intertextual_analysis}

    Please structure the appendix with the following sections:
    1. Philosophical References
    2. Literary References
    3. AI and Technology References
    4. Other Intertextual References

    For each reference, include the type, the original context, and an explanation of its significance in the video.

    Use Markdown formatting for better readability.
    """

    save_prompt(prompt, "prompt_intertextual_analysis_appendix.txt")

    response = model.generate_content(prompt)
    appendix = response.text
    print(f"Generated intertextual analysis appendix length: {len(appendix)}")

    output_file = os.path.join(OUTPUT_DIR, "intertextual_analysis_appendix.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(appendix)
    print(f"Saved intertextual analysis appendix to {output_file}")

    return appendix


def generate_final_report(
    video_title: str, video_date: str, channel_name: str, speaker_name: str
):
    print(f"Debug: Starting final report generation for '{video_title}'")

    work_products = load_work_products(INTERIM_DIR)

    consolidated_products = {}
    for wp_type, chunks in work_products.items():
        consolidated_products[wp_type] = consolidate_chunks(chunks, wp_type)

    integrated_report = generate_integrated_report(
        consolidated_products, video_title, video_date, channel_name, speaker_name
    )

    structured_elements_appendix = generate_structured_elements_appendix(
        consolidated_products["video_analysis"]
    )
    intertextual_appendix = generate_intertextual_analysis_appendix(
        consolidated_products["intertextual_analysis"]
    )

    short_title = "".join(e for e in video_title if e.isalnum())[:12]
    output_file = os.path.join(OUTPUT_DIR, f"{short_title}_final_report.md")

    final_report = f"""
    # {video_title} - Comprehensive Analysis

    {integrated_report}

    ## Appendix A: Structured Elements from Video Analysis

    {structured_elements_appendix}

    ## Appendix B: Intertextual Analysis

    {intertextual_appendix}
    """

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    print(f"Final report generated: {output_file}")
    print(f"Debug: Final report length: {len(final_report)}")
