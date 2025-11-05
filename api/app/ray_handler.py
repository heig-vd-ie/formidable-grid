import os
from pathlib import Path
import ray
from common.setup_log import setup_logger

logger = setup_logger(__name__)

SERVER_RAY_ADDRESS = os.getenv("SERVER_RAY_ADDRESS", None)


def ray_init():
    logger.info(f"Initializing Ray with address: {SERVER_RAY_ADDRESS}")
    return ray.init(
        address=SERVER_RAY_ADDRESS,
        runtime_env={
            "working_dir": str(Path(__file__).parent.parent.resolve()),
        },
    )


def ray_shutdown():
    ray.shutdown()
