import json
import time
import logging
import asyncio
from typing import List, Dict, Optional
from models import get_gemini_flash_model_json
from api_statistics import api_stats
from error_handling import handle_exceptions, VideoProcessingError

logger = logging.getLogger(__name__)


@handle_exceptions
async def analyze_intertextual_references(transcript_analysis, chunk_start, chunk_end):
    prompt = f"""
    Analyze the following transcript for intertextual references:

    Transcript:
    {transcript_analysis}

    Identify and explain any references to literary works, philosophical concepts, historical events, scientific theories, pop culture, AI technology, research papers, internet culture, or other notable ideas.

    For each reference, provide the following information in a JSON object:
    {{
        "type": "literary/philosophical/historical/scientific/pop_culture/ai_tech/research/internet_culture/other",
        "reference": "The actual reference",
        "context": "How it was used in the video, including the approximate timestamp if possible",
        "explanation": "Detailed explanation of the reference, including its origin and broader significance",
        "relevance": "How this reference relates to the main topic of the video",
        "connections": "Any connections to other references or themes in the video"
    }}

    Ensure that the output is a valid JSON array of these objects. Do not include any text before or after the JSON array.
    """

    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            model = await get_gemini_flash_model_json()
            response = await model.generate_content_async(prompt)

            await api_stats.record_call(
                module="prompt_logic_intertextual",
                function="analyze_intertextual_references",
                start_time=start_time,
                response=response,
            )

            try:
                intertextual_analysis = json.loads(response.text)
                if not isinstance(intertextual_analysis, list):
                    raise ValueError("Response is not a JSON array")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(
                    f"JSON parsing error for chunk {chunk_start}-{chunk_end}: {str(e)}"
                )
                intertextual_analysis = [{"error": str(e), "raw_text": response.text}]

            return json.dumps(intertextual_analysis, indent=2)

        except Exception as e:
            logger.error(
                f"Error in attempt {attempt + 1} for chunk {chunk_start}-{chunk_end}: {str(e)}"
            )
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.warning("Falling back to a default structure.")
                return json.dumps(
                    [
                        {
                            "error": str(e),
                            "raw_text": response.text if "response" in locals() else "",
                        }
                    ],
                    indent=2,
                )
