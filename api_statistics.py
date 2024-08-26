# api_statistics.py

import time
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class APICallMetadata:
    module: str
    function: str
    model: str
    duration: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    prompt_feedback: Dict[str, Any] = None
    error: str = None


class APIStatistics:
    def __init__(self):
        self.calls: List[APICallMetadata] = []

    def record_call(
        self,
        module: str,
        function: str,
        start_time: float,
        response: Any,
        model: str = None,
    ):
        end_time = time.time()
        duration = end_time - start_time

        try:
            metadata = self._extract_metadata(response)
            call_data = APICallMetadata(
                module=module,
                function=function,
                duration=duration,
                model=model or metadata.get("model", "Unknown"),
                **metadata,
            )
        except Exception as e:
            call_data = APICallMetadata(
                module=module,
                function=function,
                duration=duration,
                model=model or "Unknown",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                error=str(e),
            )

        self.calls.append(call_data)
        print(f"Debug: API call recorded - {call_data}")

    def _extract_metadata(self, response: Any) -> Dict[str, Any]:
        try:
            print(f"Debug: Full response object: {response}")
            print(f"Debug: Response type: {type(response)}")

            # Extract usage metadata using the correct approach for Gemini
            usage_metadata = response.result.usage_metadata
            if usage_metadata:
                print(f"Debug: UsageMetadata found: {usage_metadata}")
                return {
                    "model": getattr(response, "model", "Unknown"),
                    "input_tokens": usage_metadata.prompt_token_count,
                    "output_tokens": usage_metadata.candidates_token_count,
                    "total_tokens": usage_metadata.total_token_count,
                    "prompt_feedback": getattr(response, "prompt_feedback", None),
                    "error": None,
                }
            else:
                print("Debug: No usage_metadata attribute found")
                return {
                    "model": getattr(response, "model", "Unknown"),
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "prompt_feedback": getattr(response, "prompt_feedback", None),
                    "error": "No usage data found",
                }

        except AttributeError as e:
            print(f"Debug: AttributeError in _extract_metadata - {str(e)}")
            return {
                "model": "Unknown",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "prompt_feedback": None,
                "error": str(e),
            }
        except Exception as e:
            print(f"Debug: Unexpected error in _extract_metadata - {str(e)}")
            return {
                "model": "Unknown",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "prompt_feedback": None,
                "error": str(e),
            }

    def generate_report(self) -> str:
        report = "API Call Statistics:\n\n"
        report += f"{'Module':<20} {'Function':<25} {'Model':<20} {'Duration (s)':<15} {'Input Tokens':<15} {'Output Tokens':<15} {'Total Tokens':<15} {'Error':<20}\n"
        report += "-" * 145 + "\n"

        for call in self.calls:
            call_dict = asdict(call)
            report += f"{call_dict['module']:<20} {call_dict['function']:<25} {call_dict['model']:<20} {call_dict['duration']:<15.2f} {call_dict['input_tokens']:<15} {call_dict['output_tokens']:<15} {call_dict['total_tokens']:<15} {call_dict['error'] if call_dict['error'] else 'None':<20}\n"

        return report

    def save_report(self, filename: str):
        with open(filename, "w") as f:
            json.dump([asdict(call) for call in self.calls], f, indent=2)


api_stats = APIStatistics()
