import os
import json
import re
import base64
import asyncio
import time
import logging
from moviepy.editor import VideoFileClip
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from models import get_gemini_flash_model_text

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def sanitize_filename(title):
    sanitized = re.sub(r"[^\w\s-]", "", title)
    sanitized = re.sub(r"\s+", "_", sanitized)
    return sanitized[:30]


def parse_analysis_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    logger.debug(f"Parsing content from {txt_path}")

    elements = []
    slides = content.split("**Slide")
    for slide in slides[1:]:  # Skip the first split as it's before the first "**Slide"
        match = re.search(r"(\d+:\d+)\*\*\s*\n\s*(.+?)(?:\n|$)", slide, re.DOTALL)
        if match:
            timestamp_str, title = match.groups()
            minutes, seconds = map(int, timestamp_str.split(":"))
            timestamp = minutes * 60 + seconds
            elements.append({"timestamp": timestamp, "title": title.strip()})

    logger.debug(f"Parsed elements: {elements}")
    return elements


def get_video_for_timestamp(video_chunks, timestamp):
    for chunk in video_chunks:
        match = re.search(r"_chunk_(\d+)-(\d+)", chunk)
        if match:
            start, end = map(int, match.groups())
            if start * 60 <= timestamp < end * 60:
                return chunk
    return None


async def capture_screenshot(video_path, timestamp, output_path):
    with VideoFileClip(video_path) as video:
        chunk_start = int(re.search(r"_chunk_(\d+)-", video_path).group(1)) * 60
        relative_timestamp = timestamp - chunk_start
        screenshot_time = min(
            relative_timestamp + 1, video.duration - 0.1
        )  # Subtract 0.1 to avoid potential out-of-bounds issues
        frame = video.get_frame(screenshot_time)
        img = Image.fromarray(frame)
        img.save(output_path, format="PNG")


async def upload_image(path):
    return await asyncio.to_thread(genai.upload_file, path=path)


async def process_image(path):
    if os.path.getsize(path) > 20 * 1024 * 1024:  # 20MB
        return await upload_image(path)
    else:
        with open(path, "rb") as image_file:
            return {
                "mime_type": "image/png",
                "data": base64.b64encode(image_file.read()).decode("utf-8"),
            }


async def analyze_image_batch(image_paths, max_retries=3, retry_delay=5):
    model = await get_gemini_flash_model_text()

    image_data_list = await asyncio.gather(
        *[process_image(path) for path in image_paths]
    )

    prompt = f"""
    Analyze each of the {len(image_paths)} presentation slides in detail:
    1. Describe the overall layout and design of the slide.
    2. Identify the main title or topic of the slide.
    3. List and explain any bullet points or key text elements.
    4. Describe any visual elements like charts, graphs, or images.
    5. Interpret the main message or concept of the slide.
    6. Note any relevant context or background information that can be inferred.
    7. Identify any key terms, jargon, or technical language used.

    Provide a comprehensive description for each slide that captures all relevant information. Your descriptions should be detailed enough to serve as a substitute for the visual content in a report.

    Format your response as a JSON array of objects:
    {{
        "slide_number": 1,
        "title": "Main title of the slide",
        "description": "Detailed description of the slide content",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "visual_elements": "Description of any charts, graphs, or images",
        "main_message": "Interpretation of the slide's main concept"
    }}

    Ensure that your response is a valid JSON array. Do not include any markdown formatting or code block indicators.
    """

    for attempt in range(max_retries):
        try:
            response = await model.generate_content_async(image_data_list + [prompt])
            logger.debug(
                f"API Response: {response.text[:500]}..."
            )  # Log the first 500 characters of the response

            try:
                # Remove potential markdown formatting
                json_str = response.text.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]

                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(
                    f"Error: Invalid JSON response (Attempt {attempt + 1}/{max_retries})"
                )
                logger.error(
                    f"Response text: {response.text[:500]}..."
                )  # Log the first 500 characters of the invalid response

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        "Max retries reached. Falling back to default response."
                    )
                    return [
                        {
                            "slide_number": i + 1,
                            "title": "Error",
                            "description": "Unable to analyze image.",
                            "key_points": [],
                            "visual_elements": "",
                            "main_message": "",
                        }
                        for i in range(len(image_paths))
                    ]
        except Exception as e:
            logger.error(f"Unexpected error during API call: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached. Falling back to default response.")
                return [
                    {
                        "slide_number": i + 1,
                        "title": "Error",
                        "description": f"Error: {str(e)}",
                        "key_points": [],
                        "visual_elements": "",
                        "main_message": "",
                    }
                    for i in range(len(image_paths))
                ]


async def process_element(input_dir, video_chunks, element, output_dir):
    timestamp = element["timestamp"]
    title = element["title"]
    filename = f"{sanitize_filename(title)}_{timestamp:.2f}.png"
    output_path = os.path.join(output_dir, filename)

    video_chunk = get_video_for_timestamp(video_chunks, timestamp)
    if video_chunk:
        video_path = os.path.join(input_dir, video_chunk)
        await capture_screenshot(video_path, timestamp, output_path)

        # Add metadata
        img = Image.open(output_path)
        metadata = PngInfo()
        metadata.add_text("timestamp", str(timestamp))
        metadata.add_text("title", title)
        metadata.add_text("size", f"{img.width}x{img.height}")
        metadata.add_text("format", "PNG")
        img.save(output_path, format="PNG", pnginfo=metadata)

        return output_path
    else:
        logger.warning(
            f"No matching video chunk found for timestamp {timestamp}. Skipping."
        )
        return None


async def capture_structured_elements(input_dir, video_chunks, elements, output_dir):
    tasks = [
        process_element(input_dir, video_chunks, element, output_dir)
        for element in elements
    ]
    captured_images = await asyncio.gather(*tasks)
    return [img for img in captured_images if img is not None]


async def process_image_batches(all_image_paths, batch_size=10):
    all_descriptions = []
    for i in range(0, len(all_image_paths), batch_size):
        batch = all_image_paths[i : i + batch_size]
        batch_descriptions = await analyze_image_batch(batch)
        all_descriptions.extend(batch_descriptions)
        logger.info(
            f"Processed batch {i//batch_size + 1} of {(len(all_image_paths)-1)//batch_size + 1}"
        )
    return all_descriptions


def sort_slides_by_timestamp(all_captured_images, all_image_descriptions):
    # Extract timestamps from image filenames
    timestamps = [
        float(os.path.basename(img).split("_")[-1].split(".")[0])
        for img in all_captured_images
    ]

    # Create a list of tuples: (timestamp, image_path, description)
    sorted_slides = sorted(
        zip(timestamps, all_captured_images, all_image_descriptions), key=lambda x: x[0]
    )

    return sorted_slides


async def generate_markdown_report(
    output_dir, all_captured_images, all_image_descriptions
):
    markdown_content = "# Structured Elements Picture Report\n\n"

    # Sort slides by timestamp
    sorted_slides = sort_slides_by_timestamp(
        all_captured_images, all_image_descriptions
    )

    for i, (timestamp, img_path, desc) in enumerate(sorted_slides, start=1):
        relative_path = os.path.relpath(img_path, output_dir)
        img_filename = os.path.basename(img_path)

        # Extract the original title from the filename
        original_title = "_".join(img_filename.split("_")[:-1]).replace("_", " ")

        markdown_content += (
            f"## Slide {i}: {original_title} (Timestamp: {timestamp:.2f}s)\n\n"
        )
        markdown_content += f"![{original_title}]({relative_path})\n\n"
        markdown_content += f"**Title (from analysis):** {desc['title']}\n\n"
        markdown_content += f"**Description:** {desc['description']}\n\n"
        markdown_content += "**Key Points:**\n"
        for point in desc["key_points"]:
            markdown_content += f"- {point}\n"
        markdown_content += f"\n**Visual Elements:** {desc['visual_elements']}\n\n"
        markdown_content += f"**Main Message:** {desc['main_message']}\n\n"
        markdown_content += "---\n\n"

    report_path = os.path.join(output_dir, "picture_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(f"Markdown report generated: {report_path}")
    return report_path


async def main():
    input_dir = "./input"
    interim_dir = "./interim"
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)

    video_chunks = [f for f in os.listdir(input_dir) if f.endswith(".mp4")]
    analysis_file = "wp_SteelmanningtheDoome_consolidated_video_analysis.txt"

    logger.debug(f"Video chunks found: {video_chunks}")
    logger.debug(f"Using analysis file: {analysis_file}")

    analysis_path = os.path.join(interim_dir, analysis_file)
    elements = parse_analysis_txt(analysis_path)

    all_captured_images = await capture_structured_elements(
        input_dir, video_chunks, elements, output_dir
    )

    if not all_captured_images:
        logger.warning(
            "No images were captured. Check if the analysis file contains the expected information."
        )
        return

    # Process all captured images in batches
    all_image_descriptions = await process_image_batches(all_captured_images)

    # Generate markdown report
    report_path = await generate_markdown_report(
        output_dir, all_captured_images, all_image_descriptions
    )

    # Save all image descriptions to a single file (keeping this for reference)
    with open(
        os.path.join(output_dir, "image_descriptions.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(all_image_descriptions, f, indent=2)

    logger.info("Processing complete. Check the output directory for results.")


if __name__ == "__main__":
    asyncio.run(main())
