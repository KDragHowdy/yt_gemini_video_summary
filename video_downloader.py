import os
import yt_dlp
from datetime import datetime
from pytube import YouTube
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


def get_video_info(video_id):
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        return yt.title, yt.length
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None, None


def download_youtube_video(
    video_id: str, output_dir: str, chunk_duration=10 * 60
) -> tuple:
    """
    Downloads a YouTube video and extracts relevant metadata.

    Args:
        video_id (str): The ID of the YouTube video to download.
        output_dir (str): The directory where the video will be saved.
        chunk_duration (int): Duration of each video chunk in seconds.

    Returns:
        tuple: chunks, video_title, video_date, channel_name, speaker_name
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            video_title = info_dict.get("title", "Unknown Title")
            upload_date = info_dict.get("upload_date")
            channel_name = info_dict.get("uploader", "Unknown Channel")
            description = info_dict.get("description", "")

            # Format upload date to YYYY-MM-DD
            if upload_date:
                video_date = datetime.strptime(upload_date, "%Y%m%d").strftime(
                    "%Y-%m-%d"
                )
            else:
                video_date = "Unknown Date"

            # Speaker name extraction logic
            speaker_name = extract_speaker_name(description, channel_name)

            print(f"Video successfully downloaded: {filename}")

            # Split the video into chunks
            chunks = split_video_into_chunks(filename, chunk_duration)

            # Remove the original file
            os.remove(filename)
            print(f"Removed original file: {filename}")

            return chunks, video_title, video_date, channel_name, speaker_name

    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None, None, None, None, None


def extract_speaker_name(description: str, channel_name: str) -> str:
    """
    Extracts the speaker's name from the video description if available.

    Args:
        description (str): The video description.
        channel_name (str): The channel name, used as a fallback.

    Returns:
        str: The speaker's name.
    """
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


def split_video_into_chunks(filename, chunk_duration):
    video = VideoFileClip(filename)
    duration = video.duration
    chunks = []
    for i in range(0, int(duration), chunk_duration):
        start = i
        end = min(i + chunk_duration, duration)
        chunk_filename = f"{os.path.splitext(filename)[0]}_chunk_{int(i//60):03d}-{int(end//60):03d}.mp4"
        ffmpeg_extract_subclip(filename, start, end, targetname=chunk_filename)
        chunks.append(chunk_filename)
        print(f"Created chunk: {chunk_filename}")
    video.close()
    return chunks


# Make sure to export all necessary functions
__all__ = [
    "get_video_info",
    "download_youtube_video",
    "extract_speaker_name",
    "split_video_into_chunks",
]
