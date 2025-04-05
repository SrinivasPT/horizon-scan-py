import asyncio
import json

from common.config import load_producer_config
from common.logging_config import configure_logging, get_logger
from pipelines.pipeline import build_producer_pipeline

# Configure logging for the application
configure_logging()
logger = get_logger(__name__)


async def main():
    # Load the scan config
    scan_config = load_producer_config("config/scan_config.json")

    # Debug: log the loaded config
    logger.debug(f"Loaded scan config: {json.dumps(scan_config, indent=2)}")

    pipeline = build_producer_pipeline()

    initial_state = {
        "scan_config": scan_config,
        "batch_size": 2,
        "current_batch": 0,
        "raw_content": {},
        "documents": {},  # Changed to dict to match State TypedDict in state.py
    }

    # Log initial state (without large content)
    logger.info(f"Initial state structure: scan_config length={len(initial_state['scan_config'])}")

    state = await pipeline.ainvoke(initial_state)

    # Check the documents in the final state
    doc_count = (
        len(state["documents"])
        if isinstance(state["documents"], list)
        else sum(len(docs) for docs in state["documents"].values())
    )
    logger.info(f"Processed {doc_count} documents")


if __name__ == "__main__":
    asyncio.run(main())
