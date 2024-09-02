import asyncio
from pytube import YouTube


async def get_video_info(video_id):
    try:
        yt = await asyncio.to_thread(
            YouTube, f"https://www.youtube.com/watch?v={video_id}"
        )
        return yt.title, yt.length
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None, None


# Note: We're not implementing download_youtube_video here as it's handled in mini_video_processor.py
