# api_statistics.py

import time
from dataclasses import dataclass, asdict
import json
import asyncio


@dataclass
class APICallMetadata:
    module: str
    function: str
    duration: float
    input_tokens: int
    output_tokens: int
    total_tokens: int


class APIStatistics:
    def __init__(self):
        self.calls = []
        self.lock = asyncio.Lock()

    async def record_call(
        self, module: str, function: str, start_time: float, response
    ):
        end_time = time.time()
        duration = end_time - start_time

        print(f"Debug: Full response object: {response}")
        print(f"Debug: Response type: {type(response)}")

        try:
            usage_metadata = response.usage_metadata
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
            total_tokens = usage_metadata.total_token_count
        except AttributeError as e:
            print(f"Debug: Error accessing usage_metadata: {e}")
            input_tokens = output_tokens = total_tokens = 0

        call_data = APICallMetadata(
            module=module,
            function=function,
            duration=duration,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

        async with self.lock:
            self.calls.append(call_data)
        print(f"Debug: API call recorded - {call_data}")

    def generate_report(self) -> str:
        report = "API Call Statistics:\n\n"
        report += f"{'Module':<20} {'Function':<25} {'Duration (s)':<15} {'Input Tokens':<15} {'Output Tokens':<15} {'Total Tokens':<15}\n"
        report += "-" * 105 + "\n"

        for call in self.calls:
            call_dict = asdict(call)
            report += f"{call_dict['module']:<20} {call_dict['function']:<25} {call_dict['duration']:<15.2f} {call_dict['input_tokens']:<15} {call_dict['output_tokens']:<15} {call_dict['total_tokens']:<15}\n"

        return report

    async def save_report(self, filename: str):
        async with self.lock:
            with open(filename, "w") as f:
                json.dump([asdict(call) for call in self.calls], f, indent=2)


api_stats = APIStatistics()
