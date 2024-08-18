import google.generativeai as genai
import time
import os
from datetime import datetime

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_content(prompt, video_file=None):
    try:
        # Estimate tokens
        estimated_tokens = len(prompt) // 4
        if video_file:
            estimated_tokens += 1000  # Placeholder estimate for video file
        print(f"Estimated tokens for this call: {estimated_tokens}")

        if video_file:
            response = model.generate_content(
                [video_file, prompt], request_options={"timeout": 600}
            )
        else:
            response = model.generate_content(prompt, request_options={"timeout": 600})

        if response.prompt_feedback:
            print(f"Prompt feedback: {response.prompt_feedback}")

        return response.text

    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return f"Error in analysis: {str(e)}"


def analyze_video_content(video_file, chunk_start, chunk_end):
    print(f"Debug: Entering analyze_video_content function")
    print(f"Debug: video_file = {video_file}")
    print(f"Debug: chunk_start = {chunk_start}")
    print(f"Debug: chunk_end = {chunk_end}")

    prompt = f"""
    Analyze the visual content of the video from {chunk_start} to {chunk_end} minutes, focusing specifically on structured presentation elements such as slides, graphs, charts, code snippets, or any organized text/visual information.

    For each structured element you identify:
    1. Describe the type of element (e.g., slide, graph, chart, code snippet).
    2. Provide the timestamp or time range when it appears.
    3. Recreate the content of the element as accurately as possible, including:
       - For slides: Reproduce the text, bullet points, and describe any images.
       - For graphs/charts: Describe the type of graph, axes labels, data points, and trends.
       - For code snippets: Reproduce the code as exactly as possible.
       - For other structured elements: Provide a detailed description or reproduction.

    Ignore general background visuals or footage of the speaker unless they contain relevant structured information.

    Format the output as a numbered list of structured elements, like this:

    1. Element Type: [Type]
       Timestamp: [Time]
       Content:
       [Detailed reproduction or description of the element]

    2. Element Type: [Type]
       Timestamp: [Time]
       Content:
       [Detailed reproduction or description of the element]

    ... and so on for each identified structured element.
    """
    return generate_content(prompt, video_file)


def analyze_transcript(transcript, chunk_start, chunk_end):
    print(f"Debug: Entering analyze_transcript function")
    print(f"Debug: transcript length = {len(transcript)}")
    print(f"Debug: chunk_start = {chunk_start}")
    print(f"Debug: chunk_end = {chunk_end}")

    prompt = f"""
    Analyze the following transcript content from {chunk_start} to {chunk_end} minutes:

    Transcript: {transcript}

    Please provide a detailed list of observations that captures the essence of the spoken content, including:
    1. Key points and information presented
    2. Notable quotes or statements
    3. Names of speakers or people mentioned (if identifiable)

    Format the output as a numbered list of observations, maintaining chronological order.
    """
    return generate_content(prompt)


def analyze_combined_video_and_transcript_wp(
    video_file, transcript, chunk_start, chunk_end, video_id, video_title
):
    print(f"Debug: Entering analyze_combined_video_and_transcript_wp function")
    print(f"Debug: video_file = {video_file}")
    print(f"Debug: transcript length = {len(transcript)}")
    print(f"Debug: chunk_start = {chunk_start}")
    print(f"Debug: chunk_end = {chunk_end}")
    print(f"Debug: video_id = {video_id}")
    print(f"Debug: video_title = {video_title}")

    video_analysis = analyze_video_content(video_file, chunk_start, chunk_end)
    transcript_analysis = analyze_transcript(transcript, chunk_start, chunk_end)

    save_interim_work_product(
        video_analysis,
        video_id,
        video_title,
        f"video_analysis_chunk_{chunk_start}_{chunk_end}",
    )
    save_interim_work_product(
        transcript_analysis,
        video_id,
        video_title,
        f"transcript_analysis_chunk_{chunk_start}_{chunk_end}",
    )

    prompt = f"""
    Analyze the following video content and transcript from {chunk_start} to {chunk_end} minutes:

    Video Analysis (Structured Elements):
    {video_analysis}

    Transcript Analysis:
    {transcript_analysis}

    Please provide a detailed report that combines and synthesizes the information from both analyses, including:
    1. A chronological list of structured elements (slides, graphs, charts, code snippets) identified in the video, with their content and relevance to the spoken content.
    2. Key points and information presented, referencing the relevant visual elements where applicable.
    3. Notable quotes or statements, integrated naturally into the context and linked to visual elements if relevant.
    4. Overall flow and structure of the video segment, highlighting how the visual elements support or illustrate the spoken content.

    Format the report in Markdown, using appropriate headings and structure.
    Ensure that each structured visual element is clearly presented and explained in the context of the spoken content.
    """

    summary = generate_content(prompt, video_file)
    save_interim_work_product(
        summary, video_id, video_title, f"summary_chunk_{chunk_start}_{chunk_end}"
    )

    return summary


def save_interim_work_product(content, video_id, video_title, analysis_type):
    print(f"Debug: Entering save_interim_work_product function")
    print(f"Debug: content length = {len(content)}")
    print(f"Debug: video_id = {video_id}")
    print(f"Debug: video_title = {video_title}")
    print(f"Debug: analysis_type = {analysis_type}")

    shortened_title = "".join(e for e in video_title if e.isalnum())[:20]

    # Extract chunk information if present
    if "chunk" in analysis_type:
        chunk_info = analysis_type.split("chunk_")[1]
        chunk_start, chunk_end = chunk_info.split("_")
        chunk_start = float(chunk_start)
        chunk_end = float(chunk_end)
        filename = f"wp_{shortened_title}_{analysis_type.split('_')[0]}_chunk_{int(chunk_start)}_{int(chunk_end)}.txt"
    else:
        filename = f"wp_{shortened_title}_{analysis_type}.txt"

    interim_dir = "./interim"
    os.makedirs(interim_dir, exist_ok=True)

    file_path = os.path.join(interim_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved {analysis_type} interim work product: {filename}")
    return filename
