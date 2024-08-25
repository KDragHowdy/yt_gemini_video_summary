import os
import json
from typing import List, Dict
from models import get_gemini_flash_model_text, get_gemini_flash_model_json

BASE_DIR = r"C:\Users\kevin\repos\yt_gemini_video_summary"
INTERIM_DIR = os.path.join(BASE_DIR, "interim")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def load_work_products(interim_dir: str) -> Dict[str, List[str]]:
    work_products = {
        "video_analysis": [],
        "transcript_analysis": [],
        "intertextual_analysis": [],
        "summary": [],
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
                    elif "summary_chunk" in filename:
                        work_products["summary"].append(content)
                        print(
                            f"Debug: Loaded summary from {filename} (length: {len(content)})"
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

    if work_product_type == "intertextual_analysis":
        prompt = f"""
        Consolidate the following {work_product_type} chunks into a single coherent JSON document:

        {'\n\n'.join(chunks)}

        Instructions:
        1. Combine all references from all chunks into a single JSON array.
        2. Maintain the original structure of each reference object.
        3. Ensure all unique references from each chunk are retained.
        4. Do not summarize or paraphrase the content; instead, reorganize it.

        Format the output as a valid JSON array of reference objects.
        """
    else:
        prompt = f"""
        Consolidate the following {work_product_type} chunks into a single coherent document:

        {'\n\n'.join(chunks)}

        Instructions:
        1. Identify the common headers across all chunks.
        2. For each header, combine the relevant content from all chunks, maintaining the original sequence.
        3. Present the consolidated information under a single set of headers.
        4. Ensure all unique information from each chunk is retained.
        5. Maintain the chronological order of information where applicable.
        6. Do not summarize or paraphrase the content; instead, reorganize it.

        Format the output as a well-structured Markdown document.
        """

    save_prompt(prompt, f"prompt_consolidate_{work_product_type}.txt")

    response = model.generate_content(prompt)
    consolidated = response.text
    print(f"Debug: Consolidated {work_product_type} length: {len(consolidated)}")

    output_file = os.path.join(OUTPUT_DIR, f"consolidated_{work_product_type}.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(consolidated)
    print(f"Debug: Saved consolidated {work_product_type} to {output_file}")

    return consolidated


def generate_main_content(consolidated_products: Dict[str, str]) -> str:
    print("Debug: Generating main content")
    model = get_gemini_flash_model_text()
    prompt = f"""
    Generate a comprehensive report based on the following consolidated analyses:

    Video Analysis:
    {consolidated_products['video_analysis']}

    Transcript Analysis:
    {consolidated_products['transcript_analysis']}

    Intertextual Analysis:
    {consolidated_products['intertextual_analysis']}

    Summary:
    {consolidated_products['summary']}

    Please structure the report with the following sections:
    1. Executive Summary
    2. Key Points and Insights
    3. Detailed Analysis
    4. Conclusion and Implications

    Ensure that you incorporate relevant information from all analyses in a cohesive manner.
    """

    save_prompt(prompt, "prompt_main_content.txt")

    response = model.generate_content(prompt)
    main_content = response.text
    print(f"Debug: Generated main content length: {len(main_content)}")

    output_file = os.path.join(OUTPUT_DIR, "main_content.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(main_content)
    print(f"Debug: Saved main content to {output_file}")

    return main_content


def generate_structured_elements_appendix(video_analysis: str) -> str:
    print("Debug: Generating structured elements appendix")
    model = get_gemini_flash_model_text()
    prompt = f"""
    Extract and format all structured elements (such as slides, charts, or diagrams) mentioned in the following video analysis:

    {video_analysis}

    Present these elements in a clear, organized manner suitable for an appendix.
    Use Markdown formatting for better readability.
    """

    save_prompt(prompt, "prompt_structured_elements_appendix.txt")

    response = model.generate_content(prompt)
    appendix = response.text
    print(f"Debug: Generated structured elements appendix length: {len(appendix)}")

    output_file = os.path.join(OUTPUT_DIR, "structured_elements_appendix.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(appendix)
    print(f"Debug: Saved structured elements appendix to {output_file}")

    return appendix


def generate_intertextual_analysis_appendix(intertextual_analysis: str) -> str:
    print("Debug: Generating intertextual analysis appendix")
    model = get_gemini_flash_model_text()
    prompt = f"""
    Organize and present the following intertextual analysis in a clear, structured format suitable for an appendix:

    {intertextual_analysis}

    Group related references and provide brief explanations for each.
    Use Markdown formatting for better readability.
    """

    save_prompt(prompt, "prompt_intertextual_analysis_appendix.txt")

    response = model.generate_content(prompt)
    appendix = response.text
    print(f"Debug: Generated intertextual analysis appendix length: {len(appendix)}")

    output_file = os.path.join(OUTPUT_DIR, "intertextual_analysis_appendix.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(appendix)
    print(f"Debug: Saved intertextual analysis appendix to {output_file}")

    return appendix


def generate_final_report(video_title: str):
    print(f"Debug: Starting final report generation for '{video_title}'")

    work_products = load_work_products(INTERIM_DIR)

    consolidated_products = {}
    for wp_type, chunks in work_products.items():
        consolidated_products[wp_type] = consolidate_chunks(chunks, wp_type)

    main_content = generate_main_content(consolidated_products)

    structured_elements_appendix = generate_structured_elements_appendix(
        consolidated_products["video_analysis"]
    )
    intertextual_appendix = generate_intertextual_analysis_appendix(
        consolidated_products["intertextual_analysis"]
    )

    final_report = f"""
    # {video_title} - Analysis Report

    {main_content}

    ## Appendix A: Structured Elements from Video Analysis

    {structured_elements_appendix}

    ## Appendix B: Intertextual Analysis

    {intertextual_appendix}
    """

    output_file = os.path.join(
        OUTPUT_DIR, f"{video_title.replace(' ', '_')}_final_report.md"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    print(f"Final report generated: {output_file}")
    print(f"Debug: Final report length: {len(final_report)}")


if __name__ == "__main__":
    video_title = "Forcing Functions - Constraints, Affordances, Bounds, and Systems Behavior  [SYSTEMS THINKING]"
    generate_final_report(video_title)
