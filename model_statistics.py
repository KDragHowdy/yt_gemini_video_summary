# model_statistics.py

from typing import List, Dict
import time


class ModelStatistics:
    def __init__(self):
        self.calls: List[Dict] = []

    def record_call(
        self,
        module: str,
        function: str,
        model: str,
        start_time: float,
        end_time: float,
        input_tokens: int,
        output_tokens: int,
    ):
        self.calls.append(
            {
                "module": module,
                "function": function,
                "model": model,
                "duration": end_time - start_time,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )

    def generate_report(self) -> str:
        report = "Model Call Statistics:\n\n"
        report += f"{'Module':<20} {'Function':<25} {'Model':<20} {'Duration (s)':<15} {'Input Tokens':<15} {'Output Tokens':<15}\n"
        report += "-" * 110 + "\n"

        for call in self.calls:
            report += f"{call['module']:<20} {call['function']:<25} {call['model']:<20} {call['duration']:<15.2f} {call['input_tokens']:<15} {call['output_tokens']:<15}\n"

        return report


model_stats = ModelStatistics()


def record_model_call(func):
    def wrapper(*args, **kwargs):
        module = func.__module__
        function = func.__name__
        model = args[0].__class__.__name__  # Assuming the model is the first argument

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # Estimate token counts (you may need to adjust this based on your tokenizer)
        input_tokens = len(str(args[1])) // 4  # Rough estimate
        output_tokens = len(result.text) // 4  # Rough estimate

        model_stats.record_call(
            module, function, model, start_time, end_time, input_tokens, output_tokens
        )

        return result

    return wrapper


# Apply this decorator to all model.generate_content calls in your project
