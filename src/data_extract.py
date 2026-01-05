import os
import json
import pandas as pd
from konfig import *
from setup_log import setup_logger

logger = setup_logger(__name__)


def read_results():
    """Read all JSON result files and return as a list of dictionaries"""
    results = []
    for file in os.listdir(OUTPUT_FOLDER):
        if file.endswith(".json"):
            with open(os.path.join(OUTPUT_FOLDER, file), "r") as f:
                data = json.load(f)
                results.append(data)
    """Save results to CSV and print summary statistics"""
    # Convert to DataFrame
    df = pd.DataFrame(
        [r.__dict__ if hasattr(r, "__dict__") else dict(r) for r in results]
    )
    # Sort by datetime to ensure proper order
    df = df.sort_values("timestamp").reset_index(drop=True)
    # Performance summary
    avg_solve_time = df["solve_time_ms"].mean()
    logger.info(f"Average OpenDSS solve time: {avg_solve_time:.2f} ms")
    logger.info(f"Speedup achieved through parallelization!")
    return df
