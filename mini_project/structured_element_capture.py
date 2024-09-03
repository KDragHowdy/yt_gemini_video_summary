import logging
import time
import os
import asyncio
import json
from typing import List, Tuple
from mini_models import get_gemini_flash_model_text
from moviepy.editor import VideoFileClip
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import imagehash

logger = logging.getLogger(__name__)


def seconds_to_timestamp(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def timestamp_to_seconds(timestamp: str) -> int:
    parts = timestamp.split(":")
    return int(parts[0]) * 60 + int(parts[1])


async def analyze_video_for_structured_elements(
    video_file, transcript, chunk_start, chunk_end
):
    model = await get_gemini_flash_model_text()
    prompt = f"""
    Analyze the visual content of the video for the chunk from {chunk_start} to {chunk_end} minutes, focusing on structured presentation elements such as slides, graphs, charts, code snippets, or any organized text/visual information.

    For each structured element you identify, provide a detailed JSON description with the following keys:
    1. "type": The type of element (e.g., Slide, Graph, Chart, Code Snippet, Demonstration)
    2. "timestamp": The timestamp (in MM:SS format) when the element appears
    3. "title": The identified title or main heading of the element (if any)
    4. "unique_image_description": A detailed description of any unique image on the slide (not including speaker or template graphics)
    5. "bullet_points": A list of identified bullet points or key text elements (if any)
    6. "data_description": A description of any data presented (for charts/graphs)
    7. "axis_labels": Labels for X and Y axes (for charts/graphs)
    8. "code_language": The programming language (for code snippets)
    9. "visual_elements": A list of key visual elements (e.g., images, diagrams)
    10. "color_scheme": The dominant colors used in the element
    11. "layout_structure": A brief description of the layout (e.g., "2-column", "centered")

    Pay special attention to unique images on each slide, as these will be crucial for identifying duplicate slides.

    Format your response as a list of JSON objects, each representing a structured element:
    [
        {{
            "type": "Slide",
            "timestamp": "02:30",
            "title": "Introduction to AI",
            "unique_image_description": "A detailed illustration of a human brain with digital circuits",
            "bullet_points": ["Definition of AI", "Historical context", "Key applications"],
            "data_description": null,
            "axis_labels": null,
            "code_language": null,
            "visual_elements": ["AI brain diagram"],
            "color_scheme": ["Blue", "White"],
            "layout_structure": "Centered title with bullet points and large image"
        }},
        ...
    ]

    If no structured elements are found, return an empty list: []
    """

    response = await model.generate_content_async([video_file, prompt])
    try:
        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        elements = json.loads(json_str)
        if not isinstance(elements, list):
            raise ValueError("Response is not a list")
        return elements
    except Exception as e:
        logger.error(
            f"Failed to parse JSON from model response: {response.text[:200]}..."
        )
        logger.error(f"Error: {str(e)}")
        return []


async def capture_screenshot(video_path, timestamp, output_path):
    with VideoFileClip(video_path) as video:
        frame = video.get_frame(timestamp)
        img = Image.fromarray(frame)
        img.save(output_path, format="PNG")


def compute_image_hash(image_path):
    with Image.open(image_path) as img:
        return str(imagehash.average_hash(img))


async def filter_duplicate_elements(elements, image_paths):
    unique_elements = []
    unique_hashes = set()

    for element, image_path in zip(elements, image_paths):
        image_hash = compute_image_hash(image_path)
        if image_hash not in unique_hashes:
            unique_hashes.add(image_hash)
            unique_elements.append(element)

    return unique_elements


async def analyze_image_batch(image_paths):
    model = await get_gemini_flash_model_text()
    image_data_list = []
    for path in image_paths:
        with open(path, "rb") as image_file:
            image_data_list.append(
                {"mime_type": "image/png", "data": image_file.read()}
            )

    prompt = f"""
    Analyze each of the {len(image_paths)} images in detail:
    1. Describe the overall layout and content of the image.
    2. Identify any text, diagrams, or visual elements present.
    3. Interpret the main message or concept presented in the image.
    4. Describe any unique or notable images on the slide (excluding speaker or template graphics).

    Format your response as a list of JSON objects, one for each image:
    [
        {{
            "timestamp": "MM:SS",
            "description": "One-sentence description of the element",
            "analysis": "Detailed analysis of the image content",
            "unique_image_analysis": "Description of any unique images on the slide"
        }},
        ...
    ]
    """

    response = await model.generate_content_async(image_data_list + [prompt])
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        logger.error(
            f"Failed to parse JSON from model response: {response.text[:200]}..."
        )
        return []


async def process_structured_elements(
    video_chunks: List[str],
    video_id: str,
    video_title: str,
    duration_minutes: float,
    transcript: str,
    interim_dir: str,
    output_dir: str,
) -> Tuple[str, str]:
    logger.info("Starting to process structured elements")
    all_elements = []
    for i, chunk_path in enumerate(video_chunks):
        chunk_start = i * 10
        chunk_end = min((i + 1) * 10, duration_minutes)
        chunk_transcript = transcript[
            int(chunk_start * 60 * 10) : int(chunk_end * 60 * 10)
        ]

        logger.info(
            f"Analyzing chunk {i+1}/{len(video_chunks)} ({chunk_start}-{chunk_end} minutes)"
        )
        elements = await analyze_video_for_structured_elements(
            chunk_path, chunk_transcript, chunk_start, chunk_end
        )
        all_elements.extend(elements)

    # Capture screenshots
    image_paths = []
    for element in all_elements:
        try:
            timestamp_seconds = timestamp_to_seconds(element["timestamp"])
            output_path = os.path.join(
                interim_dir,
                f"{element['type']}_{element['timestamp'].replace(':', '_')}.png",
            )
            chunk_index = timestamp_seconds // 600
            chunk_timestamp = timestamp_seconds % 600
            await capture_screenshot(
                video_chunks[chunk_index], chunk_timestamp, output_path
            )
            image_paths.append(output_path)
        except ValueError as e:
            logger.error(f"Error processing timestamp: {e}")
            continue

    # Filter out duplicate elements based on image hashes
    filtered_elements = await filter_duplicate_elements(all_elements, image_paths)

    if not filtered_elements:
        logger.info("No structured elements found in the video")
        return (
            "No structured elements report generated",
            "No structured elements found.",
        )

    # Save the filtered list of timestamps and descriptions
    timestamps_json_path = os.path.join(interim_dir, "filtered_timestamps.json")
    with open(timestamps_json_path, "w") as f:
        json.dump(filtered_elements, f, indent=2)
    logger.info(f"Filtered timestamps and descriptions saved to {timestamps_json_path}")

    # Analyze images
    image_descriptions = await analyze_image_batch(image_paths)

    # Save image analysis results
    analysis_json_path = os.path.join(interim_dir, "image_analysis.json")
    with open(analysis_json_path, "w") as f:
        json.dump(image_descriptions, f, indent=2)
    logger.info(f"Image analysis saved to {analysis_json_path}")

    # Generate mini_final_picture_report
    report_path = os.path.join(output_dir, "mini_final_picture_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Final Picture Report for '{video_title}'\n\n")
        for element, image_path, description in zip(
            filtered_elements, image_paths, image_descriptions
        ):
            f.write(f"## Timestamp: {element['timestamp']}\n\n")
            f.write(
                f"![{element.get('title', 'No title')}]({os.path.basename(image_path)})\n\n"
            )
            f.write(f"**Type:** {element.get('type', 'Unknown')}\n\n")
            f.write(f"**Title:** {element.get('title', 'No title')}\n\n")
            if element.get("unique_image_description"):
                f.write(
                    f"**Unique Image Description:** {element['unique_image_description']}\n\n"
                )
            if element.get("bullet_points"):
                f.write("**Bullet Points:**\n")
                for point in element["bullet_points"]:
                    f.write(f"- {point}\n")
                f.write("\n")
            if element.get("data_description"):
                f.write(f"**Data Description:** {element['data_description']}\n\n")
            if element.get("axis_labels"):
                f.write(f"**Axis Labels:** {element['axis_labels']}\n\n")
            if element.get("code_language"):
                f.write(f"**Code Language:** {element['code_language']}\n\n")
            if element.get("visual_elements"):
                f.write(
                    f"**Visual Elements:** {', '.join(element['visual_elements'])}\n\n"
                )
            f.write(
                f"**Color Scheme:** {', '.join(element.get('color_scheme', ['Unknown']))}\n\n"
            )
            f.write(
                f"**Layout Structure:** {element.get('layout_structure', 'Unknown')}\n\n"
            )
            f.write(f"**Detailed Analysis:** {description['analysis']}\n\n")
            if description.get("unique_image_analysis"):
                f.write(
                    f"**Unique Image Analysis:** {description['unique_image_analysis']}\n\n"
                )
            f.write("\n---\n\n")  # Page break

    logger.info(f"Final picture report generated: {report_path}")
    return report_path, "Structured elements found and processed"
