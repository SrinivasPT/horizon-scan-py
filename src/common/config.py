import json
import logging
from typing import List

from model.state import ScanConfigItem


def load_producer_config(config_file: str) -> List[ScanConfigItem]:
    try:
        with open(config_file, "r") as f:
            config_data = json.load(f)

        # Transform the raw config items into ScanConfigItem format
        scan_config = []
        for item in config_data:
            if "source" in item and "url" in item:
                # Create parser_config with only relevant fields
                parser_config = {k: item[k] for k in ["parser", "tableSelector"] if k in item}

                # Handle columns if they exist
                if "columns" in item:
                    parser_config["columns"] = item["columns"]

                # Create the config item
                config_item = {
                    "source": item["source"],
                    "title": item.get("title", item["source"]),
                    "url": item["url"],
                    "parser_config": parser_config,
                    "defaults": item.get("defaults", {}),
                }
                scan_config.append(config_item)

        return scan_config

    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        raise
