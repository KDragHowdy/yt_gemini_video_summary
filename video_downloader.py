import os
import yt_dlp
from datetime import datetime
from pytube import YouTube
from moviepy.editor import VideoFileClip
import asyncio
import logging

logger = logging.getLogger(__name__)


async def get_video_info(video_id):
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        return yt.title, yt.length
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None, None


async def download_youtube_video(
    video_id: str, output_dir: str, chunk_duration=10 * 60
) -> tuple:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestvideo[height<=480][fps<=24]/best[height<=480][fps<=24]",  # Lower resolution and frame rate
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "noplaylist": True,  # Ensure only a single video is downloaded
        "noaudio": True,  # Do not download audio
        "limit-rate": "1000K",  # Limit the download bitrate
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = await asyncio.to_thread(ydl.extract_info, url, download=True)
            filename = ydl.prepare_filename(info_dict)
            video_title = info_dict.get("title", "Unknown Title")
            upload_date = info_dict.get("upload_date")
            channel_name = info_dict.get("uploader", "Unknown Channel")
            description = info_dict.get("description", "")

            if upload_date:
                video_date = datetime.strptime(upload_date, "%Y%m%d").strftime(
                    "%Y-%m-%d"
                )
            else:
                video_date = "Unknown Date"

            speaker_name = await extract_speaker_name(description, channel_name)

            logger.info(f"Video successfully downloaded: {filename}")

            chunks = await split_video_into_chunks(filename, chunk_duration)

            os.remove(filename)
            logger.info(f"Removed original file: {filename}")

            return chunks, video_title, video_date, channel_name, speaker_name

    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None, None, None, None, None


async def extract_speaker_name(description: str, channel_name: str) -> str:
    import re

    patterns = [
        r"Speaker[:\-]\s*(.+)",
        r"Hosted by[:\-]\s*(.+)",
        r"Presented by[:\-]\s*(.+)",
        r"By[:\-]\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return channel_name


async def split_video_into_chunks(filename, chunk_duration):
    video = VideoFileClip(filename, audio=False)  # Changed to exclude audio
    duration = video.duration
    chunks = []
    for i in range(0, int(duration), chunk_duration):
        start = i
        end = min(i + chunk_duration, duration)
        chunk_filename = f"{os.path.splitext(filename)[0]}_chunk_{int(i//60):03d}-{int(end//60):03d}.mp4"

        subclip = video.subclip(start, end)  # Using the subclip method of VideoFileClip
        await asyncio.to_thread(
            subclip.write_videofile, chunk_filename, codec="libx264"
        )

        chunks.append(chunk_filename)
        logger.info(f"Created chunk: {chunk_filename}")
    video.close()
    return chunks


__all__ = [
    "get_video_info",
    "download_youtube_video",
    "extract_speaker_name",
    "split_video_into_chunks",
]
