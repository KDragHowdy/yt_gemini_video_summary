# models.py

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
import time
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = time.time()
            self.calls = [call for call in self.calls if now - call < self.period]
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.period - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            self.calls.append(time.time())


GEMINI_FLASH_LIMITER = RateLimiter(max_calls=60, period=60)
GEMINI_PRO_LIMITER = RateLimiter(max_calls=2, period=60)

# Safety settings to allow all content
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


class AsyncGenerativeModel:
    def __init__(self, model_name, generation_config, safety_settings):
        self.model = genai.GenerativeModel(
            model_name,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

    async def generate_content_async(self, prompt):
        return await asyncio.to_thread(self.model.generate_content, prompt)


async def get_gemini_flash_model_text():
    await GEMINI_FLASH_LIMITER.wait()
    return AsyncGenerativeModel(
        "gemini-1.5-flash-exp-0827",  # Updated to latest experimental version
        generation_config={
            "temperature": 0.6,
            "top_p": 0.9,
            "top_k": 40,
        },
        safety_settings=SAFETY_SETTINGS,
    )


async def get_final_report_model_text():
    await GEMINI_PRO_LIMITER.wait()
    return AsyncGenerativeModel(
        "gemini-1.5-pro-exp-0827",  # Updated to latest experimental version
        generation_config={
            "temperature": 0.7
            "top_p": 0.9,
            "top_k": 40,
        },
        safety_settings=SAFETY_SETTINGS,
    )
