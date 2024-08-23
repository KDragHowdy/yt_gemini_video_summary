# models.py
import google.generativeai as genai
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


GEMINI_PRO_LIMITER = RateLimiter(max_calls=2, period=60)
GEMINI_FLASH_LIMITER = RateLimiter(max_calls=60, period=60)


def get_gemini_pro_model():
    GEMINI_PRO_LIMITER.wait()
    return genai.GenerativeModel(
        "gemini-1.5-pro-exp-0801",
        generation_config={"response_mime_type": "application/json"},
    )


def get_gemini_flash_model():
    GEMINI_FLASH_LIMITER.wait()
    return genai.GenerativeModel(
        "gemini-1.5-flash", generation_config={"response_mime_type": "application/json"}
    )
