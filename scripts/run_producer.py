import asyncio
from src.pipelines.producer import build_producer_pipeline
from src.common.config import load_producer_config


async def main():
    config = load_producer_config("config/app_config.json")
    pipeline = build_producer_pipeline()

    initial_state = {
        "source_urls": config["source_urls"],
        "batch_size": 2,
        "current_batch": 0,
        "raw_content": {},
    }
    await pipeline.ainvoke(initial_state)


if __name__ == "__main__":
    asyncio.run(main())
