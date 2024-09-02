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
        "gemini-1.5-flash",  # Experimental version: "gemini-1.5-flash-exp-0827"
        generation_config={
            "temperature": 0.6,
            "top_p": 0.9,
            "top_k": 40,
        },
        safety_settings=SAFETY_SETTINGS,
    )


async def get_gemini_flash_model_json():
    return AsyncGenerativeModel(
        "gemini-1.5-flash-exp-0827",  # Experimental version: "gemini-1.5-flash-exp-0827"
        generation_config={
            "temperature": 0.6,
            "top_p": 0.9,
            "top_k": 40,
            "response_mime_type": "application/json",
        },
        safety_settings=SAFETY_SETTINGS,
    )


async def get_gemini_pro_model_text():
    return AsyncGenerativeModel(
        "gemini-1.5-pro-exp-0827",  # Experimental version: "gemini-1.5-pro-exp-0827"
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
        },
        safety_settings=SAFETY_SETTINGS,
    )


async def get_gemini_pro_model_json():
    return AsyncGenerativeModel(
        "gemini-1.5-pro",  # Experimental version: "gemini-1.5-pro-exp-0827"
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "key_points": {"type": "array", "items": {"type": "string"}},
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"],
                    },
                },
                "required": ["summary", "key_points", "sentiment"],
            },
        },
        safety_settings=SAFETY_SETTINGS,
    )
