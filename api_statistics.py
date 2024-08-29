# api_statistics.py

import time
from dataclasses import dataclass, asdict, field
import json
import asyncio
from typing import List, Dict, Optional
import aiofiles
from utils import debug_print


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


@dataclass
class ProcessNode:
    name: str
    start_time: float
    end_time: float
    duration: float
    parent: Optional["ProcessNode"] = None
    children: List["ProcessNode"] = field(default_factory=list)


class APIStatistics:
    def __init__(self):
        self.calls: List[APICallMetadata] = []
        self.processes: List[ProcessMetadata] = []
        self.lock = asyncio.Lock()
        self.root = ProcessNode("Total Script", 0, 0, 0)
        self.call_counter = 0
        self.minute_start = time.time()

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
            debug_print(f"Error accessing usage_metadata: {e}")
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
            self.call_counter += 1
            current_time = time.time()
            time_elapsed = current_time - self.minute_start
            if time_elapsed >= 60:
                self.call_counter = 1
                self.minute_start = current_time
            debug_print(
                f"API call counter: {self.call_counter}, Time elapsed: {time_elapsed:.2f}s"
            )
        debug_print(f"API call recorded - {call_data}")

    async def wait_for_rate_limit(self):
        async with self.lock:
            current_time = time.time()
            time_elapsed = current_time - self.minute_start
            if time_elapsed >= 60:
                self.call_counter = 0
                self.minute_start = current_time
            elif self.call_counter >= 14:
                wait_time = 30  # 30-second cool-off
                debug_print(
                    f"Approaching rate limit. Waiting for {wait_time:.2f} seconds."
                )
                await asyncio.sleep(wait_time)
                self.call_counter = 0
                self.minute_start = time.time()
            elif self.call_counter >= 10:
                wait_time = 15  # 15-second cool-off
                debug_print(f"Nearing rate limit. Waiting for {wait_time:.2f} seconds.")
                await asyncio.sleep(wait_time)
            self.call_counter += 1
            debug_print(
                f"Current API call counter: {self.call_counter}, Time elapsed: {time_elapsed:.2f}s"
            )

    async def record_api_interaction(self, interaction_type: str):
        async with self.lock:
            self.call_counter += 1
            current_time = time.time()
            time_elapsed = current_time - self.minute_start
            if time_elapsed >= 60:
                self.call_counter = 1
                self.minute_start = current_time
            debug_print(
                f"API interaction: {interaction_type}, Counter: {self.call_counter}, Time elapsed: {time_elapsed:.2f}s"
            )

    async def record_process(
        self,
        process_name: str,
        start_time: float,
        end_time: float,
        parent: Optional[str] = None,
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
        debug_print(f"Process recorded - {process_data}")

        node = ProcessNode(process_name, start_time, end_time, duration)
        if parent:
            parent_node = self._find_node(self.root, parent)
            if parent_node:
                parent_node.children.append(node)
                node.parent = parent_node
        else:
            self.root.children.append(node)

        self.root.end_time = max(self.root.end_time, end_time)
        self.root.duration = self.root.end_time - self.root.start_time

    def _find_node(self, current_node: ProcessNode, name: str) -> Optional[ProcessNode]:
        if current_node.name == name:
            return current_node
        for child in current_node.children:
            result = self._find_node(child, name)
            if result:
                return result
        return None

    def generate_report(self) -> str:
        report = "API Call Statistics:\n\n"
        report += self._generate_api_call_statistics()
        report += "\nProcess Timings:\n\n"
        report += self._generate_process_timings()
        report += "\nHigh-Level Process Summary:\n\n"
        report += self._generate_high_level_summary()
        report += (
            f"\nTotal Script Duration: {self._calculate_total_duration():.2f} seconds\n"
        )
        return report

    def _generate_api_call_statistics(self) -> str:
        stats = f"{'Module':<20} {'Function':<25} {'Duration (s)':<15} {'Input Tokens':<15} {'Output Tokens':<15} {'Total Tokens':<15}\n"
        stats += "-" * 105 + "\n"

        for call in self.calls:
            call_dict = asdict(call)
            stats += f"{call_dict['module']:<20} {call_dict['function']:<25} {call_dict['duration']:<15.2f} {call_dict['input_tokens']:<15} {call_dict['output_tokens']:<15} {call_dict['total_tokens']:<15}\n"

        return stats

    def _generate_process_timings(self) -> str:
        timings = f"{'Process Name':<30} {'Start Time':<20} {'End Time':<20} {'Duration (s)':<15}\n"
        timings += "-" * 85 + "\n"

        for process in self.processes:
            process_dict = asdict(process)
            timings += f"{process_dict['process_name']:<30} {process_dict['start_time']:<20.2f} {process_dict['end_time']:<20.2f} {process_dict['duration']:<15.2f}\n"

        return timings

    def _generate_high_level_summary(self) -> str:
        high_level_processes = [
            "Video Info Retrieval",
            "Video Download",
            "Video Processing",
            "Final Report Generation",
        ]
        summary = f"{'Process Name':<30} {'Duration (s)':<15}\n"
        summary += "-" * 45 + "\n"
        for process in high_level_processes:
            duration = sum(
                p.duration for p in self.processes if p.process_name == process
            )
            summary += f"{process:<30} {duration:<15.2f}\n"
        return summary

    def _calculate_total_duration(self) -> float:
        return max(p.end_time for p in self.processes) - min(
            p.start_time for p in self.processes
        )

    async def generate_report_async(self) -> str:
        return self.generate_report()

    async def save_report(self, filename: str):
        report = self.generate_report()
        async with self.lock:
            async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                await f.write(report)
        debug_print(f"API statistics report saved to: {filename}")

    def generate_timeline_data(self):
        data = []
        self._generate_timeline_data_recursive(self.root, data, 0)
        return data

    def _generate_timeline_data_recursive(
        self, node: ProcessNode, data: List, level: int
    ):
        data.append(
            {
                "name": node.name,
                "start": node.start_time,
                "end": node.end_time,
                "level": level,
            }
        )
        for child in node.children:
            self._generate_timeline_data_recursive(child, data, level + 1)


api_stats = APIStatistics()
