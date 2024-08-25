import time
import os
from datetime import datetime
from models import get_gemini_flash_model_json, get_gemini_flash_model_text


def generate_content(prompt, video_file=None, use_json=False):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            estimated_tokens = len(prompt) // 4
            if video_file:
                estimated_tokens += 1000  # Placeholder estimate for video file
            print(f"Estimated tokens for this call: {estimated_tokens}")

            model = (
                get_gemini_flash_model_json()
                if use_json
                else get_gemini_flash_model_text()
            )

            if video_file:
                response = model.generate_content([video_file, prompt])
            else:
                response = model.generate_content(prompt)

            if response.prompt_feedback:
                print(f"Prompt feedback: {response.prompt_feedback}")

            if not response.text:
                raise ValueError("Response was blocked or empty. Check safety ratings.")

            return response.text

        except Exception as e:
            print(f"Error generating content (attempt {attempt + 1}): {str(e)}")
            if attempt == max_retries - 1:
                return f"Error in analysis: {str(e)}"
            time.sleep(2**attempt)  # Exponential backoff


def analyze_video_content(video_file, chunk_start, chunk_end):
    prompt = f"""
    Analyze the visual content of the video for the chunk from {chunk_start} to {chunk_end} minutes, focusing on structured presentation elements such as slides, graphs, charts, code snippets, or any organized text/visual information.

    For each structured element you identify:
    1. Describe the type of element (e.g., slide, graph, chart, code snippet).
    2. Provide the timestamp or time range when it appears.
    3. Recreate the content of the element as accurately as possible, including:
       - For slides: Reproduce the text, bullet points, and describe any images.
       - For graphs/charts: Describe the type of graph, axes labels, data points, and trends.
       - For code snippets: Reproduce the code as exactly as possible.
       - For other structured elements: Provide a detailed description or reproduction.

    Format your response in Markdown, using appropriate headings, subheadings, and formatting to recreate the structured elements as closely as possible.
    """
    return generate_content(prompt, video_file, use_json=False)


def analyze_transcript(transcript, chunk_start, chunk_end):
    prompt = f"""
    Analyze the following transcript content for the chunk from {chunk_start} to {chunk_end} minutes:

    Transcript: {transcript}

    Provide a detailed analysis that captures the essence of the spoken content, including:
    1. Key points and information presented
    2. Notable quotes or statements
    3. Names of speakers or people mentioned (if identifiable)
    4. Any significant topics or themes discussed

    Format your response in Markdown, using appropriate headings, subheadings, and bullet points.
    """
    return generate_content(prompt, use_json=False)


# ... (rest of the file remains unchanged)


def analyze_combined_video_and_transcript_wp(
    video_analysis,
    transcript_analysis,
    intertextual_analysis,
    chunk_start,
    chunk_end,
    video_id,
    video_title,
):
    prompt = f"""
    Analyze the following video content, transcript, and intertextual analysis for the 10-minute chunk from {chunk_start} to {chunk_end} minutes:

    Video Analysis (Structured Elements):
    {video_analysis}

    Transcript Analysis:
    {transcript_analysis}

    Intertextual Analysis:
    {intertextual_analysis}

    Please provide a detailed report that combines and synthesizes the information from all analyses, including:
    1. A chronological list of structured elements (slides, graphs, charts, code snippets) identified in the video, with their content and relevance to the spoken content.
    2. Key points and information presented, referencing the relevant visual elements where applicable.
    3. Notable quotes or statements, integrated naturally into the context and linked to visual elements if relevant.
    4. Intertextual references identified, explaining their significance in the context of the video content.
    5. Overall flow and structure of the video segment, highlighting how the visual elements support or illustrate the spoken content.

    Format the report in Markdown, using appropriate headings and structure.
    Ensure that each structured visual element is clearly presented and explained in the context of the spoken content and any relevant intertextual references.
    """

    return generate_content(prompt)


def save_interim_work_product(content, video_id, video_title, analysis_type):
    print(f"Debug: Entering save_interim_work_product function")
    print(f"Debug: content length = {len(content)}")
    print(f"Debug: video_id = {video_id}")
    print(f"Debug: video_title = {video_title}")
    print(f"Debug: analysis_type = {analysis_type}")

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

    print(f"Saved {analysis_type} interim work product: {filename}")
    return filename


__all__ = [
    "generate_content",
    "analyze_video_content",
    "analyze_transcript",
    "analyze_combined_video_and_transcript_wp",
    "save_interim_work_product",
]
