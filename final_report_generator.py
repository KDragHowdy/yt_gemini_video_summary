import os
import json
from typing import List, Dict
from models import get_final_report_model_json, get_final_report_model_text

OUTPUT_DIR = r"C:\Users\kevin\repos\yt_gemini_video_summary\output"


def load_work_products(output_dir: str) -> Dict[str, List[str]]:
    """
    Load all work products from the specified output directory.
    """
    work_products = {
        "video_analysis": [],
        "transcript_analysis": [],
        "intertextual_analysis": [],
        "summary": [],
    }

    for filename in os.listdir(output_dir):
        if filename.endswith(".txt"):
            for wp_type in work_products.keys():
                if wp_type in filename:
                    with open(
                        os.path.join(output_dir, filename), "r", encoding="utf-8"
                    ) as f:
                        work_products[wp_type].append(f.read())

    return work_products


def consolidate_chunks(chunks: List[str], work_product_type: str) -> str:
    """
    Use LLM to consolidate chunks of a specific work product type.
    """
    model = get_final_report_model_text()
    prompt = f"Consolidate the following {work_product_type} chunks into a coherent summary:\n\n"
    prompt += "\n\n".join(chunks)

    response = model.generate_content(prompt)
    return response.text


def generate_main_content(consolidated_products: Dict[str, str]) -> str:
    """
    Generate the main content of the report using consolidated work products.
    """
    model = get_final_report_model_text()
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

    response = model.generate_content(prompt)
    return response.text


def generate_structured_elements_appendix(video_analysis: str) -> str:
    """
    Generate the appendix for structured elements from video analysis.
    """
    model = get_final_report_model_text()
    prompt = f"""
    Extract and format all structured elements (such as slides, charts, or diagrams) mentioned in the following video analysis:

    {video_analysis}

    Present these elements in a clear, organized manner suitable for an appendix.
    Use Markdown formatting for better readability.
    """

    response = model.generate_content(prompt)
    return response.text


def generate_intertextual_analysis_appendix(intertextual_analysis: str) -> str:
    """
    Generate the appendix for intertextual analysis.
    """
    model = get_final_report_model_text()
    prompt = f"""
    Organize and present the following intertextual analysis in a clear, structured format suitable for an appendix:

    {intertextual_analysis}

    Group related references and provide brief explanations for each.
    Use Markdown formatting for better readability.
    """

    response = model.generate_content(prompt)
    return response.text


def generate_final_report(video_title: str):
    """
    Main function to generate the final report.
    """
    # Load work products
    work_products = load_work_products(OUTPUT_DIR)

    # Consolidate chunks for each work product type
    consolidated_products = {
        wp_type: consolidate_chunks(chunks, wp_type)
        for wp_type, chunks in work_products.items()
    }

    # Generate main content
    main_content = generate_main_content(consolidated_products)

    # Generate appendices
    structured_elements_appendix = generate_structured_elements_appendix(
        consolidated_products["video_analysis"]
    )
    intertextual_appendix = generate_intertextual_analysis_appendix(
        consolidated_products["intertextual_analysis"]
    )

    # Combine all parts into the final report
    final_report = f"""
    # {video_title} - Analysis Report

    {main_content}

    ## Appendix A: Structured Elements from Video Analysis

    {structured_elements_appendix}

    ## Appendix B: Intertextual Analysis

    {intertextual_appendix}
    """

    # Save the final report
    output_file = os.path.join(
        OUTPUT_DIR, f"{video_title.replace(' ', '_')}_final_report.md"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)

    print(f"Final report generated: {output_file}")


if __name__ == "__main__":
    video_title = "Sample Video Title"  # This should be dynamically set based on the processed video
    generate_final_report(video_title)
