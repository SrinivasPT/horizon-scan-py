import json
import logging
from typing import List

from model.state import ScanConfigItem


def load_producer_config(config_file: str) -> List[ScanConfigItem]:
    try:
        with open(config_file, "r") as f:
            config_data = json.load(f)

        return [
            {
                "source": item["source"],
                "title": item.get("title", item["source"]),
                "url": item["url"],
                "parser_config": item.get("parser_config", {}),
                "defaults": item.get("defaults", {}),
            }
            for item in config_data
            if "source" in item and "url" in item
        ]

    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        raise
