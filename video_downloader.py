import yt_dlp
import os
from pytube import YouTube


def get_video_info(video_id):
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        return yt.title, yt.length
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None, None


def download_youtube_video(video_id, output_dir):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        print(f"Video successfully downloaded to {filename}")
        return filename
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None
