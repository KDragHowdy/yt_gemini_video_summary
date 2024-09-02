import os
import asyncio
import json
import time
import logging
import aiofiles
from typing import List, Dict
from models import get_gemini_flash_model_text, get_gemini_pro_model_text
from api_statistics import api_stats

BASE_DIR = r"C:\Users\kevin\repos\yt_gemini_video_summary"
INTERIM_DIR = os.path.join(BASE_DIR, "interim")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

logger = logging.getLogger(__name__)


async def load_work_products(interim_dir: str):
    work_products = {
        "video_analysis": None,
        "transcript_analysis": None,
        "intertextual_analysis": None,
    }

    for filename in os.listdir(interim_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(interim_dir, filename)
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    if "consolidated_video_analysis" in filename:
                        work_products["video_analysis"] = content
                    elif "consolidated_transcript_analysis" in filename:
                        work_products["transcript_analysis"] = content
                    elif "consolidated_intertextual_analysis" in filename:
                        work_products["intertextual_analysis"] = content
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")

    return work_products


async def generate_integrated_report(
    consolidated_products: Dict[str, str], video_info: Dict
):
    total_input_chars = sum(len(product) for product in consolidated_products.values())
    target_word_count = min(
        1800, int(video_info["duration"] * 50 + total_input_chars / 100)
    )

    prompt = f"""
    Create a comprehensive report on "{video_info['title']}" by {video_info['speaker']}, aired on {video_info['date']} on {video_info['channel']}. 
    The video is approximately {video_info['duration']:.0f} minutes long.
    
    Do not include a title, just begin with the introduction.
    
    Use the following consolidated analyses to create a flowing, essay-like discussion of the topic.  These analyses notes meant to capture notes from the video to serve as input for the report.
    
    Transcript Analysis: This is notes from the full audio dialogue from the video.  It provides details, facts, sequence and argument and description development presented sequentially through the video {consolidated_products['transcript_analysis']}
    
    Video Analysis: This is a recreation of any structured visual elements presented in the video, like slides, graphs or other exhibit.{consolidated_products['video_analysis']}
    
    Intertextual Analysis: This is an exhibit capturing any unique language, jargon, references, and memetic language from the video. The exhibit explains the meaning and relationship of the languiage to the segment being discussed to provide further context for generating the details of the report, as the terms are likely assumed to be understood and not actually explained in the dialogue and can add the flavor of the speakers meaning. {consolidated_products['intertextual_analysis']}

    Your report should:
    1. Identify the overarching storyline or themes that emerge from the transcript notes, including any additional context provided by the recreated elements of the video analysis and the intertextual analyses.
    2. Present the speaker's views as our own, building a coherent argument or description that follows the linear flow and development of ideas in the video. We should aim to provide a detailed, insightful analysis that captures the essence of the content includind the idea development to support our conclusions.
    3. Include a significant amount of direct facts, quotes, intertextual references naturally throughout the report to help make the points being discusses through their relevance and significance from the input thorughout the report so as to provide a rich flavor to the report, not a generic summary document.
    4. Use the identified overarching themes to expand on the linear flow presented in the transcript. This helps present the both the flow of the video and the deeper insights and connections.
    5. Develop the argument or description progressively, mirroring the structure of the video while expanding on key points.
    6. Use a scholarly tone that demonstrates deep understanding and critical analysis of the content. Remeber, you are taking the notes as work product and creating a detailed report, not a summary.
    7. Aim for a word count of approximately {target_word_count} words for the main body of the report.

    Structure the report as follows:
    1. Introduction
    2. Main Body (use appropriate subheadings based on the video's content and identified themes)
    3. Conclusion

    Formatting:
    - Use Markdown for structuring.
    - Use "" for direct quotes from the video.
    - Use bold for emphasizing the intertextual reference.

    Aim for a comprehensive, engaging, and insightful report that captures the essence of the video's content while providing a deeper analysis guided by the identified themes.
    """

    model = await get_gemini_pro_model_text()
    await api_stats.wait_for_rate_limit()
    start_time = time.time()
    response = await model.generate_content_async(prompt)
    await api_stats.record_call(
        module="final_report_generator",
        function="generate_integrated_report",
        start_time=start_time,
        response=response,
    )

    return response.text


async def generate_structured_elements_appendix(video_analysis: str):
    prompt = f"""
    Present a well formatted Appendix of Structured Video Elements based on this analysis.  This appendix is a detailed recreation of the structured visual elements presented in the video, such as slides, graphs, or other exhibits.  Use Markdown formatting for clarity and readability.:

    {video_analysis}

    Only show structured visual elements (ignore unstructured video descriptions, such as segments mainly showing just the speaker talking or looping or "b-role" video)
    
    """

    model = await get_gemini_pro_model_text()
    await api_stats.wait_for_rate_limit()
    start_time = time.time()
    response = await model.generate_content_async(prompt)
    await api_stats.record_call(
        module="final_report_generator",
        function="generate_structured_elements_appendix",
        start_time=start_time,
        response=response,
    )

    return response.text


async def generate_intertextual_analysis_appendix(intertextual_analysis: str):
    prompt = f"""
    "Presednt a well formatted appendix of Intertextual References based on this analysis:

    {intertextual_analysis}

    Use Markdown formatting for clarity and readability.
    """

    model = await get_gemini_pro_model_text()
    await api_stats.wait_for_rate_limit()
    start_time = time.time()
    response = await model.generate_content_async(prompt)
    await api_stats.record_call(
        module="final_report_generator",
        function="generate_intertextual_analysis_appendix",
        start_time=start_time,
        response=response,
    )

    return response.text


async def generate_final_report(video_info: Dict):
    work_products = await load_work_products(INTERIM_DIR)

    # Generate report sections in parallel
    integrated_report_task = generate_integrated_report(work_products, video_info)
    structured_elements_task = generate_structured_elements_appendix(
        work_products["video_analysis"]
    )
    intertextual_appendix_task = generate_intertextual_analysis_appendix(
        work_products["intertextual_analysis"]
    )

    (
        integrated_report,
        structured_elements_appendix,
        intertextual_appendix,
    ) = await asyncio.gather(
        integrated_report_task, structured_elements_task, intertextual_appendix_task
    )

    final_report = f"""
    # {video_info['title']}

    {integrated_report}

    {structured_elements_appendix}

    {intertextual_appendix}
    """

    short_title = "".join(e for e in video_info["title"] if e.isalnum())[:12]
    output_file = os.path.join(OUTPUT_DIR, f"{short_title}_final_report.md")

    async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
        await f.write(final_report)

    logger.info(f"Final report generated: {output_file}")
    return output_file


async def main(
    video_id, video_title, video_date, channel_name, speaker_name, duration_minutes
):
    video_info = {
        "id": video_id,
        "title": video_title,
        "date": video_date,
        "channel": channel_name,
        "speaker": speaker_name,
        "duration": duration_minutes,
    }
    await generate_final_report(video_info)


if __name__ == "__main__":
    asyncio.run(
        main(
            video_id,
            video_title,
            video_date,
            channel_name,
            speaker_name,
            duration_minutes,
        )
    )
