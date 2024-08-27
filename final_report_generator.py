# final_report_generator.py

import os
import time
import json
import asyncio
import aiofiles
from typing import List, Dict
from models import get_final_report_model_text, get_gemini_flash_model_text
from api_statistics import api_stats

BASE_DIR = r"C:\\Users\\kevin\\repos\\yt_gemini_video_summary"
INTERIM_DIR = os.path.join(BASE_DIR, "interim")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


async def save_prompt(prompt: str, filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(prompt)
    print(f"Debug: Saved prompt to {filename}")


async def save_consolidated_work_product(content: str, work_product_type: str):
    filename = f"consolidated_{work_product_type}.txt"
    file_path = os.path.join(OUTPUT_DIR, filename)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)
    print(f"Debug: Saved consolidated {work_product_type} to {filename}")


async def load_work_products(interim_dir: str) -> Dict[str, List[str]]:
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
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    content = content.strip()
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


async def consolidate_chunks(chunks: List[str], work_product_type: str) -> str:
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
        try:
            model = await get_gemini_flash_model_text()
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

            await save_prompt(prompt, f"prompt_consolidate_{work_product_type}.txt")

            start_time = time.time()
            response = await model.generate_content_async(prompt)

            print(f"Debug: Response object type: {type(response)}")
            print(f"Debug: Response object attributes: {dir(response)}")
            print(f"Debug: Response object __dict__: {response.__dict__}")

            await api_stats.record_call(
                module="final_report_generator",
                function="consolidate_chunks",
                start_time=start_time,
                response=response,
            )

            consolidated = response.text

        except Exception as e:
            print(f"Error consolidating chunks: {str(e)}")
            consolidated = f"Error in consolidation: {str(e)}"

    print(f"Debug: Consolidated {work_product_type} length: {len(consolidated)}")
    await save_consolidated_work_product(consolidated, work_product_type)

    return consolidated


async def generate_integrated_report(
    consolidated_products: Dict[str, str],
    video_title: str,
    video_date: str,
    channel_name: str,
    speaker_name: str,
    video_duration_minutes: float,
) -> str:
    total_input_chars = sum(len(product) for product in consolidated_products.values())
    target_word_count = max(
        1000, int(video_duration_minutes * 50 + total_input_chars / 100)
    )

    prompt = f"""
    Create a comprehensive report on "{video_title}" by {speaker_name}, aired on {video_date} on {channel_name}. 
    The video is approximately {video_duration_minutes:.0f} minutes long.
    
    Use the following consolidated analyses to create a flowing, essay-like discussion of the topic:
    Video Analysis: {consolidated_products['video_analysis']}
    Transcript Analysis: {consolidated_products['transcript_analysis']}
    Intertextual Analysis: {consolidated_products['intertextual_analysis']}

    Your report should:
    1. Identify the overarching storyline or themes that emerge from the video, transcript, and intertextual analyses.
    2. Present the speaker's views as our own, building a coherent argument or description that follows the linear flow and development of ideas in the video.
    3. Use the identified overarching themes to expand on this linear flow, providing deeper insights and connections.
    4. Integrate visual elements, quotes, and intertextual references by explaining their relevance and significance, rather than presenting them as separate exhibits.
    5. Develop the argument or description progressively, mirroring the structure of the video while expanding on key points.
    6. Use a scholarly tone that demonstrates deep understanding and critical analysis of the content.
    7. Aim for a word count of approximately {target_word_count} words for the main body of the report.

    Structure the report as follows:
    1. Introduction
    2. Main Body (use appropriate subheadings based on the video's content and identified themes)
    3. Conclusion

    Formatting:
    - Use Markdown for structuring.
    - Use blockquotes (>) for direct quotes from the video.
    - Use bold for emphasizing key points.
    - Use italics for introducing intertextual references.

    Aim for a comprehensive, engaging, and insightful report that captures the essence of the video's content while providing a deeper analysis guided by the identified themes.
    """

    await save_prompt(prompt, "prompt_integrated_report.txt")

    try:
        model = await get_final_report_model_text()
        start_time = time.time()
        response = await model.generate_content_async(prompt)

        print(f"Debug: Response object type: {type(response)}")
        print(f"Debug: Response object attributes: {dir(response)}")
        print(f"Debug: Response object __dict__: {response.__dict__}")

        await api_stats.record_call(
            module="final_report_generator",
            function="generate_integrated_report",
            start_time=start_time,
            response=response,
        )

        integrated_report = response.text
        print(f"Generated integrated report length: {len(integrated_report)}")

        await save_consolidated_work_product(integrated_report, "integrated_report")

        return integrated_report

    except Exception as e:
        print(f"Error generating integrated report: {str(e)}")
        return f"Error in integrated report generation: {str(e)}"


async def generate_structured_elements_appendix(video_analysis: str) -> str:
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

    await save_prompt(prompt, "prompt_structured_elements_appendix.txt")

    try:
        model = await get_final_report_model_text()
        start_time = time.time()
        response = await model.generate_content_async(prompt)

        print(f"Debug: Response object type: {type(response)}")
        print(f"Debug: Response object attributes: {dir(response)}")
        print(f"Debug: Response object __dict__: {response.__dict__}")

        await api_stats.record_call(
            module="final_report_generator",
            function="generate_structured_elements_appendix",
            start_time=start_time,
            response=response,
        )

        appendix = response.text
        print(f"Generated structured elements appendix length: {len(appendix)}")

        await save_consolidated_work_product(appendix, "structured_elements_appendix")

        return appendix

    except Exception as e:
        print(f"Error generating structured elements appendix: {str(e)}")
        return f"Error in structured elements appendix generation: {str(e)}"


async def generate_intertextual_analysis_appendix(intertextual_analysis: str) -> str:
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

    await save_prompt(prompt, "prompt_intertextual_analysis_appendix.txt")

    try:
        model = await get_final_report_model_text()
        start_time = time.time()
        response = await model.generate_content_async(prompt)

        print(f"Debug: Response object type: {type(response)}")
        print(f"Debug: Response object attributes: {dir(response)}")
        print(f"Debug: Response object __dict__: {response.__dict__}")

        await api_stats.record_call(
            module="final_report_generator",
            function="generate_intertextual_analysis_appendix",
            start_time=start_time,
            response=response,
        )

        appendix = response.text
        print(f"Generated intertextual analysis appendix length: {len(appendix)}")

        await save_consolidated_work_product(appendix, "intertextual_analysis_appendix")

        return appendix

    except Exception as e:
        print(f"Error generating intertextual analysis appendix: {str(e)}")
        return f"Error in intertextual analysis appendix generation: {str(e)}"


async def generate_final_report(
    video_title: str,
    video_date: str,
    channel_name: str,
    speaker_name: str,
    video_duration_minutes: float,
):
    print(f"Debug: Starting final report generation for '{video_title}'")

    work_products = await load_work_products(INTERIM_DIR)

    consolidated_products = {}
    consolidation_tasks = []
    for wp_type, chunks in work_products.items():
        task = asyncio.create_task(consolidate_chunks(chunks, wp_type))
        consolidation_tasks.append((wp_type, task))

    for wp_type, task in consolidation_tasks:
        consolidated_products[wp_type] = await task

    integrated_report = await generate_integrated_report(
        consolidated_products,
        video_title,
        video_date,
        channel_name,
        speaker_name,
        video_duration_minutes,
    )

    structured_elements_appendix_task = asyncio.create_task(
        generate_structured_elements_appendix(consolidated_products["video_analysis"])
    )
    intertextual_appendix_task = asyncio.create_task(
        generate_intertextual_analysis_appendix(
            consolidated_products["intertextual_analysis"]
        )
    )

    structured_elements_appendix = await structured_elements_appendix_task
    intertextual_appendix = await intertextual_appendix_task

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

    async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
        await f.write(final_report)

    print(f"Final report generated: {output_file}")
    print(f"Debug: Final report length: {len(final_report)}")


if __name__ == "__main__":
    # This block is for testing purposes
    video_title = "Sample Video Title"
    video_date = "2023-08-25"
    channel_name = "Sample Channel"
    speaker_name = "John Doe"
    video_duration_minutes = 15.0
    asyncio.run(
        generate_final_report(
            video_title, video_date, channel_name, speaker_name, video_duration_minutes
        )
    )
