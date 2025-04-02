import asyncio

from pipelines.pipeline import build_producer_pipeline
from src.common.config import load_producer_config


async def main():
    scan_config = load_producer_config("config/scan_config.json")
    pipeline = build_producer_pipeline()

    initial_state = {
        "scan_config": scan_config,
        "batch_size": 2,
        "current_batch": 0,
        "raw_content": {},
    }

    await pipeline.ainvoke(initial_state)


if __name__ == "__main__":
    asyncio.run(main())
