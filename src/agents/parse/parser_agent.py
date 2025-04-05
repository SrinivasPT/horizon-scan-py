import asyncio
import json
import logging
from typing import Dict, Type

from aiohttp import ClientSession

from agents.parse.base_parser import BaseParser
from agents.parse.html_parser import HTMLParser
from agents.parse.rss_parser import RSSParser
from model.state import State

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParserAgent:
    def __init__(self):
        self.parsers: Dict[str, Type[BaseParser]] = {
            "RSS-PARSER": RSSParser,
            "HTML-PARSER": HTMLParser,
        }

    async def parse_content(self, state: State) -> Dict:
        documents = []

        if state["scan_config"] and len(state["scan_config"]) > 0:
            logger.info(f"First item in scan_config: {json.dumps(state['scan_config'][0], indent=2)}")

        async with ClientSession() as session:
            tasks = []
            for source, (url, content, content_type) in state["raw_content"].items():
                # Find the matching source config
                source_config = None
                for item in state["scan_config"]:
                    if item.get("source") == source:
                        source_config = item
                        break

                parser_type = source_config["parser_config"]["parser"]
                parser = self.parsers[parser_type]()

                tasks.append(parser.parse(content, source_config, url))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error during parsing: {result}")
                elif isinstance(result, list):
                    documents.extend(result)

        # Only return the documents instead of the entire state
        return {"documents": [doc.to_dict() for doc in documents]}
