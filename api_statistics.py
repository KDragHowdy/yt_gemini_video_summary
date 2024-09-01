from collections import deque
import time
import asyncio
import logging
import aiofiles

logger = logging.getLogger(__name__)


class APIStatistics:
    def __init__(self):
        self.flash_call_timestamps = deque(
            maxlen=60
        )  # For Gemini Flash (60 calls/minute)
        self.pro_call_timestamps = deque(maxlen=2)  # For Gemini Pro (2 calls/minute)
        self.lock = asyncio.Lock()
        self.calls = []
        self.processes = []
        self.api_interactions = []
        self.total_wait_time = 0

    async def wait_for_rate_limit(self, model_type="flash"):
        try:
            async with asyncio.timeout(30):  # 30-second timeout
                async with self.lock:
                    current_time = time.time()

                    if model_type == "flash":
                        call_timestamps = self.flash_call_timestamps
                        max_calls = 60
                    else:  # 'pro'
                        call_timestamps = self.pro_call_timestamps
                        max_calls = 2

                    if len(call_timestamps) == max_calls:
                        oldest_call = call_timestamps[0]
                        time_since_oldest = current_time - oldest_call

                        if time_since_oldest < 60:
                            wait_time = 60 - time_since_oldest
                            logger.info(
                                f"Rate limit reached for {model_type}. Waiting for {wait_time:.2f} seconds."
                            )
                            await asyncio.sleep(wait_time)
                            current_time = time.time()
                            # Log the actual wait time
                            actual_wait_time = current_time - (current_time - wait_time)
                            logger.info(
                                f"Actual wait time: {actual_wait_time:.2f} seconds"
                            )
                            self.total_wait_time += actual_wait_time

                    call_timestamps.append(current_time)
        except asyncio.TimeoutError:
            logger.error(f"Timeout while waiting for rate limit ({model_type})")
        except asyncio.CancelledError:
            logger.error(f"Rate limiting was cancelled ({model_type})")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rate limiting: {str(e)}")
            raise

    async def record_call(
        self,
        module: str,
        function: str,
        start_time: float,
        response,
        model_type="flash",
    ):
        await self.wait_for_rate_limit(model_type)
        end_time = time.time()
        duration = end_time - start_time

        try:
            if hasattr(response, "usage_metadata"):
                usage_metadata = response.usage_metadata
                input_tokens = usage_metadata.prompt_token_count
                output_tokens = usage_metadata.candidates_token_count
                total_tokens = usage_metadata.total_token_count
            else:
                input_tokens = output_tokens = total_tokens = 0
                logger.warning(
                    f"Response object does not have usage_metadata attribute in {function}"
                )
                logger.debug(f"Response object: {response}")
                logger.debug(f"Response object type: {type(response)}")
                logger.debug(f"Response object attributes: {dir(response)}")
        except AttributeError as e:
            logger.error(f"Error accessing usage_metadata: {e}")
            logger.debug(f"Response object: {response}")
            logger.debug(f"Response object type: {type(response)}")
            logger.debug(f"Response object attributes: {dir(response)}")
            input_tokens = output_tokens = total_tokens = 0

        call_data = {
            "module": module,
            "function": function,
            "duration": duration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

        async with self.lock:
            self.calls.append(call_data)
        logger.debug(f"API call recorded - {call_data}")

    async def record_process(
        self, process_name: str, start_time: float, end_time: float
    ):
        duration = end_time - start_time
        process_data = {
            "process_name": process_name,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
        }
        async with self.lock:
            self.processes.append(process_data)
        logger.debug(f"Process recorded - {process_data}")

    async def record_api_interaction(self, interaction_type: str):
        async with self.lock:
            self.api_interactions.append(
                {"type": interaction_type, "timestamp": time.time()}
            )
        logger.debug(f"API interaction recorded: {interaction_type}")

    async def generate_report_async(self):
        total_calls = len(self.calls)
        total_duration = sum(call["duration"] for call in self.calls)
        total_input_tokens = sum(call["input_tokens"] for call in self.calls)
        total_output_tokens = sum(call["output_tokens"] for call in self.calls)

        report = f"API Statistics Report\n"
        report += f"Total API calls: {total_calls}\n"
        report += f"Total duration: {total_duration:.2f} seconds\n"
        report += f"Total input tokens: {total_input_tokens}\n"
        report += f"Total output tokens: {total_output_tokens}\n"
        report += f"Total wait time due to rate limiting: {self.total_wait_time:.2f} seconds\n"

        if self.processes:
            report += "\nProcess Durations:\n"
            for process in self.processes:
                report += (
                    f"{process['process_name']}: {process['duration']:.2f} seconds\n"
                )

        return report

    async def save_report(self, filename: str):
        report = await self.generate_report_async()
        async with aiofiles.open(filename, "w") as f:
            await f.write(report)
        logger.info(f"API statistics report saved to {filename}")


api_stats = APIStatistics()
