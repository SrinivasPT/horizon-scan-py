import logging
import pprint
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from agents.parse.base_parser import BaseParser
from model.document import Document

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HTMLParser(BaseParser):

    def __init__(self):
        pass

    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        soup = BeautifulSoup(content, "html.parser")
        parser_config = config["parser_config"]
        documents = []

        try:
            rows = soup.select(parser_config["rowSelector"])
            for row in rows:
                doc = await self._parse_row(row, config, base_url)
                if doc:
                    documents.append(doc)

            logger.debug(f"Parsed documents: {pprint.pprint(documents[5])}")
            logger.info(f"Parsed {len(documents)} HTML table rows")
            return documents
        except Exception as e:
            logger.error(f"Error parsing HTML table: {str(e)}")
            return []

    async def _parse_row(self, row: Tag, scan_config: Dict, base_url: str) -> Optional[Document]:
        try:
            config = scan_config["parser_config"]
            doc = Document(**scan_config.get("defaults", {}))

            for column in config["columns"]:
                value = self._extract_column_value(row, column, base_url)
                setattr(doc, column["name"], value)

            return doc
        except Exception as e:
            logger.error(f"Error parsing row: {str(e)}")
            return None

    def _extract_column_value(self, row: Tag, column: Dict, base_url: str) -> str:
        element = row.select_one(column["selector"])
        if not element:
            return ""

        if column.get("name") == "linkToRegChangeText":
            return self._extract_link(element, base_url)
        else:
            return element.get_text(strip=True)

    def _extract_link(self, element: Tag, base_url: str) -> str:
        """Extracts URL from element or its direct <a> child."""

        # If element is already an <a> tag
        if element.name == "a" and element.has_attr("href"):
            return urljoin(base_url, element["href"])

        # Find first <a> child with href
        a_tag = element.find("a", href=True)
        if a_tag:
            return urljoin(base_url, a_tag["href"])

        return ""

    async def close(self):
        await super().close()
        if hasattr(self, "summary_parser") and self.summary_parser:
            await self.summary_parser.close()
