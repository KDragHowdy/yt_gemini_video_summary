import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
import time
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

    def wait(self):
        now = time.time()
        self.calls = [call for call in self.calls if now - call < self.period]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.period - now
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.calls.append(time.time())


GEMINI_FLASH_LIMITER = RateLimiter(max_calls=60, period=60)

# Safety settings to allow all content
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


def get_gemini_flash_model_json():
    GEMINI_FLASH_LIMITER.wait()
    return genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 1.0,
            "top_p": 1.0,
            "top_k": 40,
        },
        safety_settings=SAFETY_SETTINGS,
    )


def get_gemini_flash_model_text():
    GEMINI_FLASH_LIMITER.wait()
    return genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={
            "temperature": 1.0,
            "top_p": 1.0,
            "top_k": 40,
        },
        safety_settings=SAFETY_SETTINGS,
    )
