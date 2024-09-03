import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    return AsyncGenerativeModel(
        "gemini-1.5-flash",  # You can change this to the experimental version if needed
        generation_config={
            "temperature": 0.6,
            "top_p": 0.9,
            "top_k": 40,
        },
        safety_settings=SAFETY_SETTINGS,
    )
