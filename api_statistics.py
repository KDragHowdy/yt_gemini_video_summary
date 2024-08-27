# api_statistics.py

import time
from dataclasses import dataclass, asdict
import json
import asyncio
from typing import List, Dict
import aiofiles


@dataclass
class APICallMetadata:
    module: str
    function: str
    duration: float
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class ProcessMetadata:
    process_name: str
    start_time: float
    end_time: float
    duration: float


class APIStatistics:
    def __init__(self):
        self.calls: List[APICallMetadata] = []
        self.processes: List[ProcessMetadata] = []
        self.lock = asyncio.Lock()

    async def record_call(
        self, module: str, function: str, start_time: float, response
    ):
        end_time = time.time()
        duration = end_time - start_time

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

    async def record_process(
        self, process_name: str, start_time: float, end_time: float
    ):
        duration = end_time - start_time
        process_data = ProcessMetadata(
            process_name=process_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
        )
        async with self.lock:
            self.processes.append(process_data)
        print(f"Debug: Process recorded - {process_data}")

    def generate_report(self) -> str:
        report = "API Call Statistics:\n\n"
        report += f"{'Module':<20} {'Function':<25} {'Duration (s)':<15} {'Input Tokens':<15} {'Output Tokens':<15} {'Total Tokens':<15}\n"
        report += "-" * 105 + "\n"

        for call in self.calls:
            call_dict = asdict(call)
            report += f"{call_dict['module']:<20} {call_dict['function']:<25} {call_dict['duration']:<15.2f} {call_dict['input_tokens']:<15} {call_dict['output_tokens']:<15} {call_dict['total_tokens']:<15}\n"

        report += "\nProcess Timings:\n\n"
        report += f"{'Process Name':<30} {'Start Time':<20} {'End Time':<20} {'Duration (s)':<15}\n"
        report += "-" * 85 + "\n"

        for process in self.processes:
            process_dict = asdict(process)
            report += f"{process_dict['process_name']:<30} {process_dict['start_time']:<20.2f} {process_dict['end_time']:<20.2f} {process_dict['duration']:<15.2f}\n"

        total_duration = max(process.end_time for process in self.processes) - min(
            process.start_time for process in self.processes
        )
        report += f"\nTotal Script Duration: {total_duration:.2f} seconds\n"

        return report

    async def generate_report_async(self) -> str:
        return self.generate_report()

    async def save_report(self, filename: str):
        report = self.generate_report()
        async with self.lock:
            async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                await f.write(report)
        print(f"API statistics report saved to: {filename}")


api_stats = APIStatistics()
