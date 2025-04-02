import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from agents.parse.base_parser import BaseParser
from model.document import Document

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLParser(BaseParser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        soup = BeautifulSoup(content, "html.parser")
        documents = []

        try:
            rows = soup.select(config["tableSelector"])
            for row in rows:
                doc = await self._parse_row(row, config, base_url)
                if doc:
                    documents.append(doc)

            logger.info(f"Parsed {len(documents)} HTML table rows")
            return documents
        except Exception as e:
            logger.error(f"Error parsing HTML table: {str(e)}")
            return []

    async def _parse_row(self, row: Tag, config: Dict, base_url: str) -> Optional[Document]:
        """Parse a single row into a Document object"""
        try:
            doc = Document(**self.defaults)

            for column in config["columns"]:
                value = self._extract_column_value(row, column, base_url)

                # Handle special case for summary fetching
                if value and "linkToRegChangeText" in column["name"] and column.get("isLink"):
                    summary_config = config.get("summaryConfig")
                    if summary_config:
                        summary = await self.summary_parser.fetch_summary(value, summary_config)
                        doc.summary = summary

                setattr(doc, column["name"], value)

            return await self.process_dynamic_defaults(doc)
        except Exception as e:
            logger.error(f"Error parsing row: {str(e)}")
            return None

    def _extract_column_value(self, row: Tag, column: Dict, base_url: str) -> str:
        """Extract value from a column based on configuration"""
        element = row.select_one(column["selector"])
        if not element:
            return ""

        if column.get("attribute"):
            return element.get(column["attribute"]) or ""
        elif column.get("isLink"):
            return self._extract_link(element, base_url)
        else:
            return element.get_text(strip=True)

    def _extract_link(self, element: Tag, base_url: str) -> str:
        """Extract and normalize link from element"""
        link = element.get("href") or (element.find("a") and element.find("a").get("href")) or ""
        return urljoin(base_url, link) if link else ""

    async def close(self):
        """Close resources"""
        await super().close()
        if self.summary_parser:
            await self.summary_parser.close()
