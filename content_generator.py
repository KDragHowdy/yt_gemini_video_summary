import os
import time
from api_statistics import api_stats
from models import get_gemini_flash_model_json, get_gemini_flash_model_text


def generate_content(prompt, video_file=None, use_json=False):
    start_time = time.time()

    try:
        model = (
            get_gemini_flash_model_json() if use_json else get_gemini_flash_model_text()
        )
        response = (
            model.generate_content(prompt)
            if not video_file
            else model.generate_content([video_file, prompt])
        )

        api_stats.record_call(
            module="content_generator",
            function="generate_content",
            start_time=start_time,
            response=response,
        )

        if response.prompt_feedback:
            print(f"Prompt feedback: {response.prompt_feedback}")

        return response.text

    except Exception as e:
        api_stats.record_call(
            module="content_generator",
            function="generate_content",
            start_time=start_time,
            response=None,  # This will trigger the error handling in APIStatistics
        )
        print(f"Error generating content: {str(e)}")
        return f"Error in analysis: {str(e)}"


def analyze_video_content(video_file, chunk_start, chunk_end):
    prompt = f"""
    Analyze the visual content of the video for the chunk from {chunk_start} to {chunk_end} minutes, focusing on structured presentation elements such as slides, graphs, charts, code snippets, or any organized text/visual information.

    For each structured element you identify:
    1. Determine the type of element for use in the start of the title (e.g., "Slide:", "Graph:", "Chart:", "Code Snippet:").
    2. Provide the timestamp or time range when it appears.
    3. Recreate the content of the element as accurately as possible, including:
       - For slides: Reproduce the text, bullet points, and describe any images.
       - For graphs/charts: Describe the type of graph, axes labels, data points, and trends.
       - For code snippets: Reproduce the code as exactly as possible.
       - For other structured elements: Provide a detailed description or reproduction.

    Format your response in Markdown using appropriate headings, subheadings and formatting to recreate the structured elements as closely as possible.
    Ensure that each element is clearly presented sequentially, with a one line title based on materials presented.  For any elements that are not easily categorized, use a generic title like "Structured Element 1," "Structured Element 2,".  Do not output descriptions for any segments that are considered unstructured.
    Seperate each structured element with a blank line.
    Don't add text before or after the structured elemennts
    """
    return generate_content(prompt, video_file, use_json=False)


def analyze_transcript(transcript, chunk_start, chunk_end):
    prompt = f"""
    Analyze the following transcript content for the chunk from {chunk_start} to {chunk_end} minutes:

    Transcript: {transcript}

    Provide a detailed analysis that captures the essence of the spoken content, including:
    1. The sequential development of the arguments
    2. The key points and information presented
    3. Notable quotes or statements made by the speaker
    3. Names of speakers or people mentioned (if identifiable)
    4. Any significant topics or themes discussed
    5. Try to exclude extraneous commentary unrelated to the topic being presented.
    6. Present in a narrator style as if you were relay the content to someone else, maintaining the context of the original transcript. Try to avoid phrases like "the speaker said" or "the transcript mentions.", jsut present the content as if you were telling someone about it.
    7. Dont include any text before or after the transcript content.

    Format your response in Markdown, using appropriate headings, subheadings, and bullet points.
    """
    return generate_content(prompt, use_json=False)


def save_interim_work_product(content, video_id, video_title, analysis_type):
    print("Debug: Entering save_interim_work_product function")
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
    "save_interim_work_product",
]
