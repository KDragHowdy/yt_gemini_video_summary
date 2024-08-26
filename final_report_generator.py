# final_report_generator.py

import os
import time
import json
from typing import List, Dict
from models import get_final_report_model_text, get_gemini_flash_model_text
from api_statistics import api_stats

BASE_DIR = r"C:\\Users\\kevin\\repos\\yt_gemini_video_summary"
INTERIM_DIR = os.path.join(BASE_DIR, "interim")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def save_prompt(prompt: str, filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"Debug: Saved prompt to {filename}")


def save_consolidated_work_product(content: str, work_product_type: str):
    filename = f"consolidated_{work_product_type}.txt"
    file_path = os.path.join(OUTPUT_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Debug: Saved consolidated {work_product_type} to {filename}")


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


def consolidate_chunks(chunks: List[str], work_product_type: str) -> str:
    print(f"Debug: Consolidating {work_product_type} chunks (total: {len(chunks)})")

    if work_product_type == "intertextual_analysis":
        consolidated_data = []
        for chunk in chunks:
            try:
                chunk_data = json.loads(chunk)
                if isinstance(chunk_data, list):
                    consolidated_data.extend(chunk_data)
                elif isinstance(chunk_data, dict):
                    if "raw_text" in chunk_data:
                        consolidated_data.append(
                            {"unstructured_content": chunk_data["raw_text"]}
                        )
                    else:
                        consolidated_data.append(chunk_data)
            except json.JSONDecodeError:
                consolidated_data.append({"unstructured_content": chunk})

        consolidated = json.dumps(consolidated_data, indent=2)
    else:
        model = get_gemini_flash_model_text()
        chunks_text = "\n\n".join(chunks)
        prompt = f"""
        Consolidate the following {work_product_type} chunks into a single coherent document:

        {chunks_text}

        Instructions:
        1. Maintain the original chronological order of the content.
        2. Preserve the structure and headings from the original chunks.
        3. Combine similar or repeated information under unified headings.
        4. Ensure all unique information from each chunk is retained.
        5. Use clear transitions between different sections to maintain flow.
        6. If there are time stamps or segment markers, include them to indicate progression.

        Format the output as a well-structured Markdown document, using appropriate headings (##, ###, etc.) to reflect the content hierarchy.
        """

        save_prompt(prompt, f"prompt_consolidate_{work_product_type}.txt")

        start_time = time.time()
        response = model.generate_content(prompt)

        api_stats.record_call(
            module="final_report_generator",
            function="consolidate_chunks",
            start_time=start_time,
            response=response,
            model=model.__class__.__name__,
        )

        consolidated = response.text

    print(f"Debug: Consolidated {work_product_type} length: {len(consolidated)}")
    save_consolidated_work_product(consolidated, work_product_type)

    return consolidated


def generate_integrated_report(
    consolidated_products: Dict[str, str],
    video_title: str,
    video_date: str,
    channel_name: str,
    speaker_name: str,
) -> str:
    prompt = f"""
    Create a comprehensive report on "{video_title}" by {speaker_name}, aired on {video_date} on {channel_name}. 
    
    Use the following consolidated analyses to create a flowing, essay-like discussion of the topic:
    Video Analysis: {consolidated_products['video_analysis']}
    Transcript Analysis: {consolidated_products['transcript_analysis']}
    Intertextual Analysis: {consolidated_products['intertextual_analysis']}

    Your report should:
    1. Present the speaker's views as our own, building a coherent argument or description as developed in the video.
    2. Integrate visual elements, quotes, and intertextual references seamlessly into the discussion.
    3. Develop the argument or description progressively, mirroring the structure of the video.
    4. Use a scholarly tone that demonstrates deep understanding and critical analysis of the content.
    5. Avoid describing what the speaker did, instead present the ideas directly.

    Structure the report as follows:
    1. Introduction
    2. Main Body (use appropriate subheadings based on the video's content)
    3. Conclusion

    Formatting:
    - Use Markdown for structuring.
    - Use blockquotes (>) for direct quotes from the video.
    - Use bold for emphasizing key points.
    - Use italics for introducing intertextual references.

    Aim for a comprehensive, engaging, and insightful report that captures the essence of the video's content.
    """

    save_prompt(prompt, "prompt_integrated_report.txt")

    start_time = time.time()
    model = get_final_report_model_text()
    response = model.generate_content(prompt)

    api_stats.record_call(
        module="final_report_generator",
        function="generate_integrated_report",
        start_time=start_time,
        response=response,
        model=model.__class__.__name__,
    )

    integrated_report = response.text
    print(f"Generated integrated report length: {len(integrated_report)}")

    save_consolidated_work_product(integrated_report, "integrated_report")

    return integrated_report


def generate_structured_elements_appendix(video_analysis: str) -> str:
    prompt = f"""
    Create a detailed appendix of structured elements from the video analysis:

    {video_analysis}

    For each slide or major visual element:
    1. Create a markdown representation of the slide, including:
       - A clear title (use ## for the slide title)
       - A description of the visual elements (use italic text)
       - The main points or content of the slide (use bullet points)
    2. Provide the timestamp or time range when it appears.
    3. Explain its relevance to the video's content.

    Use markdown formatting for clarity and readability. Aim to recreate the visual structure of the slides as closely as possible using markdown syntax.
    """

    save_prompt(prompt, "prompt_structured_elements_appendix.txt")

    start_time = time.time()
    model = get_final_report_model_text()
    response = model.generate_content(prompt)

    api_stats.record_call(
        module="final_report_generator",
        function="generate_structured_elements_appendix",
        start_time=start_time,
        response=response,
        model=model.__class__.__name__,
    )

    appendix = response.text
    print(f"Generated structured elements appendix length: {len(appendix)}")

    save_consolidated_work_product(appendix, "structured_elements_appendix")

    return appendix


def generate_intertextual_analysis_appendix(intertextual_analysis: str) -> str:
    prompt = f"""
    Create a comprehensive appendix of intertextual references based on this analysis:

    {intertextual_analysis}

    For each reference:
    1. Categorize it (e.g., Philosophical, Literary, Scientific, Technological, etc.).
    2. Provide the context in which it was mentioned in the video.
    3. Explain the reference's significance to the video's content.
    4. If applicable, provide a brief background of the reference for viewers who might be unfamiliar.

    Organize the appendix by categories, and within each category, list references chronologically as they appear in the video.

    Use Markdown formatting for clarity and readability.
    """

    save_prompt(prompt, "prompt_intertextual_analysis_appendix.txt")

    start_time = time.time()
    model = get_final_report_model_text()
    response = model.generate_content(prompt)

    api_stats.record_call(
        module="final_report_generator",
        function="generate_intertextual_analysis_appendix",
        start_time=start_time,
        response=response,
        model=model.__class__.__name__,
    )

    appendix = response.text
    print(f"Generated intertextual analysis appendix length: {len(appendix)}")

    save_consolidated_work_product(appendix, "intertextual_analysis_appendix")

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


if __name__ == "__main__":
    # This block is for testing purposes
    video_title = "Sample Video Title"
    video_date = "2023-08-25"
    channel_name = "Sample Channel"
    speaker_name = "John Doe"
    generate_final_report(video_title, video_date, channel_name, speaker_name)
