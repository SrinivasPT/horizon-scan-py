import datetime
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from aiohttp import ClientSession

from model.document import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for all parsers"""

    def __init__(self, defaults: Dict[str, Any], session: ClientSession):
        self.defaults = defaults
        self.session = session
        self.env.globals.update({"new": lambda x: datetime.datetime, "Date": datetime.datetime})

    @abstractmethod
    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        pass

    async def process_dynamic_defaults(self, doc: Document) -> Document:
        """Process dynamic default values with enhanced Jinja2 templating"""
        doc_dict = doc.to_dict()
        for key, value in doc_dict.items():
            if isinstance(value, str) and "${" in value:
                try:
                    template = self.env.from_string(value)
                    doc_dict[key] = template.render(**doc_dict)
                except Exception as e:
                    logger.error(f"Error processing dynamic default {key}: {str(e)}")
        return Document(**doc_dict)
