import asyncio
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
            "HTML-TABLE-PARSER": HTMLParser,
        }

    async def parse_content(self, state: State) -> State:
        documents = []
        async with ClientSession() as session:
            tasks = []

            for source, (url, content, content_type) in state["raw_content"].items():
                source_config = next((item for item in self.config_data if item["source"] == source), None)
                if not source_config:
                    continue

                pipeline = source_config.get("pipeline", [])
                defaults = source_config.get("defaults", {})

                for stage in pipeline:
                    stage_type = stage["stage"]
                    if stage_type in self.parsers:
                        parser = self.parsers[stage_type](defaults, session)
                        tasks.append(parser.parse(content, stage.get("config", {}), url))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    documents.extend(result)

        return {**state, "documents": [doc.to_dict() for doc in documents]}
