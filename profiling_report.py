# profiling_report.py

import asyncio
import cProfile
import pstats
import io
from memory_profiler import profile as memory_profile
import time
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def run_profiler(func, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
    finally:
        pr.disable()
    s = io.StringIO()
    sortby = "cumulative"
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    return s.getvalue(), result


@memory_profile
def memory_profiled_run(func, *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        return asyncio.run(func(*args, **kwargs))
    return func(*args, **kwargs)


async def generate_profiling_report(main_function, *args, **kwargs):
    report = "Profiling and Optimization Report\n"
    report += "================================\n\n"

    # Time profiling
    start_time = time.time()
    logger.debug("Starting profiling of main function")
    profiler_output, result = await run_profiler(main_function, *args, **kwargs)
    end_time = time.time()
    logger.debug("Finished profiling of main function")

    report += f"Total execution time: {end_time - start_time:.2f} seconds\n\n"
    report += "cProfile Output:\n"
    report += "----------------\n"
    report += profiler_output
    report += "\n"

    # Memory profiling
    report += "Memory Profiling:\n"
    report += "-----------------\n"
    report += "To view memory usage, run the script with @memory_profile decorator\n"
    report += "on the main function and check the console output.\n\n"

    # Optimization suggestions
    report += "Optimization Suggestions:\n"
    report += "-------------------------\n"
    report += (
        "1. Focus on functions with high cumulative time in the cProfile output.\n"
    )
    report += (
        "2. Look for unexpected function calls or loops that might be optimized.\n"
    )
    report += "3. Consider using more efficient data structures or algorithms where applicable.\n"
    report += "4. Check for any I/O operations that could be optimized or made asynchronous.\n"
    report += "5. Investigate memory usage patterns and optimize for lower memory consumption.\n"

    # Save report
    report_filename = "profiling_report.txt"
    with open(report_filename, "w") as f:
        f.write(report)

    logger.info(f"Profiling report saved to {report_filename}")

    return result


# Example usage
if __name__ == "__main__":
    # Import your main function here
    from main import main

    # Run the profiler on your main function
    asyncio.run(generate_profiling_report(main))
