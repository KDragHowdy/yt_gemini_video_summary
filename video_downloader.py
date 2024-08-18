import yt_dlp
import os
from pytube import YouTube
from moviepy.editor import VideoFileClip


def get_video_info(video_id):
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        return yt.title, yt.length
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None, None


def download_youtube_video(
    video_id, output_dir, chunk_duration=20 * 60
):  # Default to 20 minutes
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

        # Split the video into chunks
        video = VideoFileClip(filename)
        duration = video.duration
        chunks = []
        for i in range(0, int(duration), chunk_duration):
            start = i
            end = min(i + chunk_duration, duration)
            chunk = video.subclip(start, end)
            chunk_filename = f"{os.path.splitext(filename)[0]}_chunk_{int(i//60):02d}-{int(end//60):02d}.mp4"
            chunk.write_videofile(chunk_filename)
            chunks.append(chunk_filename)
            print(f"Created chunk: {chunk_filename}")
        video.close()

        # Remove the original file
        os.remove(filename)
        print(f"Removed original file: {filename}")

        return chunks
    except Exception as e:
        print(f"Error downloading or splitting video: {str(e)}")
        import traceback

        traceback.print_exc()
        return None
