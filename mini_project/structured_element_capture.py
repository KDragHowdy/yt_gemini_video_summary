import os
import json
import asyncio
import time
import logging
from moviepy.editor import VideoFileClip
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from models import get_gemini_flash_model_text
from api_statistics import api_stats
from mini_error_handling import handle_mini_exceptions, MiniVideoProcessingError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def sanitize_filename(title):
    return "".join(e for e in title if e.isalnum())[:30]


async def analyze_video_for_structured_elements(
    video_file, transcript, chunk_start, chunk_end
):
    model = await get_gemini_flash_model_text()
    prompt = f"""
    Analyze the following video chunk from {chunk_start} to {chunk_end} minutes and the corresponding transcript:

    Transcript: {transcript}

    Identify any structured elements such as slides, graphs, charts, or code snippets. For each element:
    1. Provide the approximate timestamp (in seconds from the start of the chunk).
    2. Describe the type of element (e.g., Slide, Graph, Chart, Code Snippet).
    3. Give a brief title or description of the content.

    Format your response as a JSON array of objects:
    [
        {{
            "timestamp": 120,
            "type": "Slide",
            "title": "Introduction to Machine Learning"
        }},
        ...
    ]

    Only include clear, distinct structured elements. Do not include timestamps for general video content or speaker appearances.
    """

    start_time = time.time()
    response = await model.generate_content_async(prompt)
    await api_stats.record_call(
        module="structured_element_capture",
        function="analyze_video_for_structured_elements",
        start_time=start_time,
        response=response,
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(
            f"Failed to parse JSON from model response: {response.text[:200]}..."
        )
        return []


async def capture_screenshot(video_path, timestamp, output_path):
    with VideoFileClip(video_path) as video:
        frame = video.get_frame(timestamp)
        img = Image.fromarray(frame)
        img.save(output_path, format="PNG")


async def process_element(video_path, element, output_dir, chunk_start):
    timestamp = element["timestamp"] + (
        chunk_start * 60
    )  # Convert chunk_start to seconds
    title = element["title"]
    element_type = element["type"]
    filename = f"{sanitize_filename(title)}_{timestamp:.2f}.png"
    output_path = os.path.join(output_dir, filename)

    await capture_screenshot(video_path, element["timestamp"], output_path)

    # Add metadata
    img = Image.open(output_path)
    metadata = PngInfo()
    metadata.add_text("timestamp", str(timestamp))
    metadata.add_text("title", title)
    metadata.add_text("type", element_type)
    metadata.add_text("size", f"{img.width}x{img.height}")
    metadata.add_text("format", "PNG")
    img.save(output_path, format="PNG", pnginfo=metadata)

    return output_path, element


async def analyze_image_batch(image_paths_and_elements, max_retries=3, retry_delay=5):
    model = await get_gemini_flash_model_text()
    image_paths, elements = zip(*image_paths_and_elements)

    image_data_list = []
    for path in image_paths:
        with open(path, "rb") as image_file:
            image_data_list.append(
                {"mime_type": "image/png", "data": image_file.read()}
            )

    prompt = f"""
    Analyze each of the {len(image_paths)} presentation elements in detail:
    1. Describe the overall layout and design of the element.
    2. Identify the main title or topic.
    3. List and explain any bullet points or key text elements.
    4. Describe any visual elements like charts, graphs, or images.
    5. Interpret the main message or concept.
    6. Note any relevant context or background information that can be inferred.
    7. Identify any key terms, jargon, or technical language used.

    Provide a comprehensive description for each element that captures all relevant information.

    Format your response as a JSON array of objects:
    [
        {{
            "element_number": 1,
            "type": "Slide",
            "title": "Main title of the element",
            "description": "Detailed description of the content",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "visual_elements": "Description of any charts, graphs, or images",
            "main_message": "Interpretation of the element's main concept"
        }},
        ...
    ]

    Ensure that your response is a valid JSON array.
    """

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = await model.generate_content_async(image_data_list + [prompt])
            await api_stats.record_call(
                module="structured_element_capture",
                function="analyze_image_batch",
                start_time=start_time,
                response=response,
            )

            try:
                result = json.loads(response.text)
                for r, e in zip(result, elements):
                    r.update(e)
                return result
            except json.JSONDecodeError:
                logger.error(
                    f"Error: Invalid JSON response (Attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        "Max retries reached. Falling back to default response."
                    )
                    return [{"error": "Failed to analyze images"} for _ in image_paths]
        except Exception as e:
            logger.error(f"Unexpected error during API call: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached. Falling back to default response.")
                return [{"error": f"Error: {str(e)}"} for _ in image_paths]


async def generate_markdown_report(output_dir, all_image_descriptions):
    markdown_content = "# Structured Elements Report\n\n"

    for desc in all_image_descriptions:
        markdown_content += (
            f"## {desc['type']}: {desc['title']} (Timestamp: {desc['timestamp']}s)\n\n"
        )
        markdown_content += (
            f"![{desc['title']}]({os.path.basename(desc['image_path'])})\n\n"
        )
        markdown_content += f"**Description:** {desc['description']}\n\n"
        markdown_content += "**Key Points:**\n"
        for point in desc["key_points"]:
            markdown_content += f"- {point}\n"
        markdown_content += f"\n**Visual Elements:** {desc['visual_elements']}\n\n"
        markdown_content += f"**Main Message:** {desc['main_message']}\n\n"
        markdown_content += "---\n\n"

    report_path = os.path.join(output_dir, "structured_elements_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(f"Markdown report generated: {report_path}")
    return report_path


@handle_mini_exceptions
async def process_structured_elements(
    video_chunks,
    video_id,
    video_title,
    duration_minutes,
    transcript,
    interim_dir,
    output_dir,
):
    all_elements = []
    for i, chunk_path in enumerate(video_chunks):
        chunk_start = i * 10
        chunk_end = min((i + 1) * 10, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]

        elements = await analyze_video_for_structured_elements(
            chunk_path, chunk_transcript, chunk_start, chunk_end
        )
        all_elements.extend(elements)

    image_paths_and_elements = []
    for element in all_elements:
        chunk_index = int(element["timestamp"] // 600)  # 600 seconds = 10 minutes
        chunk_path = video_chunks[chunk_index]
        image_path, updated_element = await process_element(
            chunk_path, element, output_dir, chunk_index * 10
        )
        image_paths_and_elements.append((image_path, updated_element))

    all_image_descriptions = await analyze_image_batch(image_paths_and_elements)

    report_path = await generate_markdown_report(output_dir, all_image_descriptions)
    return report_path


if __name__ == "__main__":
    print("This script should be run as part of the mini project pipeline.")
