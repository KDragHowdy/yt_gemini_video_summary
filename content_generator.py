import os
import time
import logging
from api_statistics import api_stats
from models import get_gemini_flash_model_text, get_gemini_flash_model_json
from error_handling import handle_exceptions, VideoProcessingError

logger = logging.getLogger(__name__)


@handle_exceptions
async def generate_content(prompt, video_file=None, use_json=False):
    start_time = time.time()

    try:
        model = await (
            get_gemini_flash_model_json() if use_json else get_gemini_flash_model_text()
        )

        if video_file:
            response = await model.generate_content_async([video_file, prompt])
        else:
            response = await model.generate_content_async(prompt)

        await api_stats.record_call(
            module="content_generator",
            function="generate_content",
            start_time=start_time,
            response=response,
        )

        if hasattr(response, "prompt_feedback"):
            logger.info(f"Prompt feedback: {response.prompt_feedback}")

        return response.text

    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return f"Error in analysis: {str(e)}"


@handle_exceptions
async def analyze_video_content(video_file, chunk_start, chunk_end):
    start_time = time.time()
    prompt = f"""
    Analyze the visual content of the video for the chunk from {chunk_start} to {chunk_end} minutes, focusing on structured presentation elements such as slides, graphs, charts, code snippets, or any organized text/visual information.

    For each structured element you identify:
    1. Determine the type of element (e.g., Slide, Graph, Chart, Code Snippet, Demonstration).
    2. Provide a title with timestamp or time range when it appears.
    3. Give a brief description of the context but dont preceed the descrip with a lablel.
    3. Recreate the element in detail, including:
       - For slides: bullet points, any imagery or diagrams.
       - For graphs/charts: Type of graph, axes labels, data representation, and key trends or insights.
       - For code snippets: purpose of the code and key functions or concepts demonstrated.
       - For demonstrations: Step-by-step breakdown of what's being shown.
    

    Format your response in Markdown to recreate the structured elements as closely as possible.
    Ensure that each element is clearly presented sequentially.
    Separate each structured element with a blank line.

    Don't add any other text at the beginning or end other than your analysis.
    """
    result = await generate_content(prompt, video_file, use_json=False)
    end_time = time.time()
    await api_stats.record_process(
        f"analyze_video_content_{chunk_start:03.0f}_{chunk_end:03.0f}",
        start_time,
        end_time,
    )
    return result


@handle_exceptions
async def analyze_transcript(transcript, chunk_start, chunk_end):
    start_time = time.time()
    prompt = f"""
    Analyze the following transcript content for the chunk from {chunk_start} to {chunk_end} minutes:

    Transcript: {transcript}

    Provide a detailed analysis that captures the essence of the spoken content, including:
    1. Main Topics and Themes:
       - Identify and list the primary topics discussed.
       - Highlight any recurring themes or motifs in the speaker's discourse.

    2. Key Arguments and Points:
       - Outline the descriptions, arguments or points being made by the speaker.
       - Explain how these points are developed or supported throughout the segment and their significance.

    3. Notable Quotes:
       - Identify and transcribe verbatim at least 3-5 significant quotes.
       - For each quote, provide:
         a) The approximate timestamp.
         b) A brief explanation of its significance or context.

    4. Rhetorical Devices and Speaking Style:
       - Note any rhetorical devices or unique speaking styles employed.
       
    5. Technical or Specialized Language:
       - Highlight any technical terms, jargon, or memetic language used.
       - Briefly explain these terms if they're crucial to understanding the content.

    6. Discuss any other notable aspects of the content
    
    Format your response in Markdown in note style with any helpful headings and subheadings.  The idea is to create detail notes to be untilzide as input in generating a future report about the detailed content of the video. Your job is to get the detailed record, not to create a summaryEnsure that your analysis flows logically and captures the progression of ideas in the transcript.

    Don't add any other text at the beginning or end other than your analysis.
    """
    result = await generate_content(prompt, use_json=False)
    end_time = time.time()
    await api_stats.record_process(
        f"analyze_transcript_{chunk_start:03.0f}_{chunk_end:03.0f}",
        start_time,
        end_time,
    )
    return result


@handle_exceptions
async def save_interim_work_product(content, video_id, video_title, analysis_type):
    start_time = time.time()
    logger.debug("Entering save_interim_work_product function")
    logger.debug(f"content length = {len(content)}")
    logger.debug(f"video_id = {video_id}")
    logger.debug(f"video_title = {video_title}")
    logger.debug(f"analysis_type = {analysis_type}")

    shortened_title = "".join(e for e in video_title if e.isalnum())[:20]

    if "chunk" in analysis_type:
        chunk_info = analysis_type.split("chunk_")[1]
        chunk_start, chunk_end = chunk_info.split("_")
        chunk_start = float(chunk_start)
        chunk_end = float(chunk_end)
        filename = f"wp_{shortened_title}_{analysis_type.split('_')[0]}_chunk_{int(chunk_start):03d}_{int(chunk_end):03d}.txt"
    else:
        filename = f"wp_{shortened_title}_{analysis_type}.txt"

    interim_dir = "./interim"
    os.makedirs(interim_dir, exist_ok=True)

    file_path = os.path.join(interim_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Saved {analysis_type} interim work product: {filename}")
    end_time = time.time()
    await api_stats.record_process(
        f"save_interim_work_product_{analysis_type}", start_time, end_time
    )
    return filename


__all__ = [
    "generate_content",
    "analyze_video_content",
    "analyze_transcript",
    "save_interim_work_product",
]
