# final_report_generator.py

import os
import time
import asyncio
import aiofiles
from models import get_final_report_model_text
from api_statistics import api_stats
from error_handling import handle_exceptions, VideoProcessingError


@handle_exceptions
async def generate_final_report(
    video_title: str,
    video_date: str,
    channel_name: str,
    speaker_name: str,
    video_duration_minutes: float,
    consolidated_intertextual: str,
    consolidated_video: str,
    consolidated_transcript: str,
):
    start_time = time.time()

    prompt = f"""
    Create a comprehensive report on "{video_title}" by {speaker_name}, aired on {video_date} on {channel_name}. 
    The video is approximately {video_duration_minutes:.0f} minutes long.
    
    Use the following consolidated analyses to create a flowing, essay-like discussion of the topic:
    Video Analysis: {consolidated_video}
    Transcript Analysis: {consolidated_transcript}
    Intertextual Analysis: {consolidated_intertextual}

    Your report should:
    1. Identify the overarching storyline or themes that emerge from the video, transcript, and intertextual analyses.
    2. Present the speaker's views as our own, building a coherent argument or description that follows the linear flow and development of ideas in the video.
    3. Use the identified overarching themes to expand on this linear flow, providing deeper insights and connections.
    4. Integrate visual elements, quotes, and intertextual references by explaining their relevance and significance, rather than presenting them as separate exhibits.
    5. Develop the argument or description progressively, mirroring the structure of the video while expanding on key points.
    6. Use a scholarly tone that demonstrates deep understanding and critical analysis of the content.

    Structure the report as follows:
    1. Introduction
    2. Main Body (use appropriate subheadings based on the video's content and identified themes)
    3. Conclusion
    4. Appendix A: Structured Slides (recreate the slides and visual elements from the video analysis)
    5. Appendix B: Intertextual References (list and explain key intertextual references)

    Formatting:
    - Use Markdown for structuring.
    - Use blockquotes (>) for direct quotes from the video.
    - Use bold for emphasizing key points.
    - Use italics for introducing intertextual references.

    Aim for a comprehensive, engaging, and insightful report that captures the essence of the video's content while providing a deeper analysis guided by the identified themes.
    """

    model = await get_final_report_model_text()
    response = await model.generate_content_async(prompt)

    end_time = time.time()
    await api_stats.record_process("generate_final_report", start_time, end_time)

    return response.text


async def save_final_report(report: str, video_title: str):
    start_time = time.time()
    shortened_title = "".join(e for e in video_title if e.isalnum())[:20]
    filename = f"final_report_{shortened_title}.md"

    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(report)

    end_time = time.time()
    await api_stats.record_process("save_final_report", start_time, end_time)

    print(f"Final report saved to: {file_path}")
    return file_path


@handle_exceptions
async def generate_and_save_final_report(
    video_title: str,
    video_date: str,
    channel_name: str,
    speaker_name: str,
    video_duration_minutes: float,
    consolidated_intertextual: str,
    consolidated_video: str,
    consolidated_transcript: str,
):
    report = await generate_final_report(
        video_title,
        video_date,
        channel_name,
        speaker_name,
        video_duration_minutes,
        consolidated_intertextual,
        consolidated_video,
        consolidated_transcript,
    )
    file_path = await save_final_report(report, video_title)
    return file_path
