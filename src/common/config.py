import json
from typing import List, Dict, Any


def load_producer_config(config_file: str) -> Dict[str, Any]:
    # For this implementation, we'll read app_config.json directly
    # Later this can be modified to use the config_file parameter if needed
    with open("config/app_config.json", "r") as f:
        config_data = json.load(f)

    # Extract source identifiers and URLs from the configuration
    source_urls = []
    for item in config_data:
        if "url" in item and "source" in item:
            source_urls.append({"source": item["source"], "url": item["url"]})

    return {"source_urls": source_urls}


def load_urls(file_path: str) -> List[str]:
    with open(file_path, "r") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]
    return urls
