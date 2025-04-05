import datetime
import pprint
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from common.logging_config import get_logger
from model.document import Document

logger = get_logger(__name__, "DEBUG")


class RSSParser:
    """Specialized parser for BIS RSS feeds in RDF format."""

    # Define the specific namespaces used in BIS feeds
    NAMESPACES = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "cb": "http://www.cbwiki.net/wiki/index.php/Specification_1.1",
        "default": "http://purl.org/rss/1.0/",  # Default namespace without prefix
    }

    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        logger.info(f"Parsing BIS RSS content for {config['source']}")

        try:
            # Register namespaces for cleaner XPath expressions
            self._register_namespaces()

            root = ET.fromstring(content)
            items = self._extract_rdf_items(root)
            documents = [self._create_document(item, config) for item in items]

            logger.info(f"Successfully parsed {len(documents)} BIS RSS items")
            logger.debug(f"Parsed documents: {pprint.pformat(documents)}")

            return documents

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing RSS: {str(e)}", exc_info=True)
        return []

    def _register_namespaces(self) -> None:
        for prefix, uri in self.NAMESPACES.items():
            if prefix != "default":
                ET.register_namespace(prefix, uri)

    def _extract_rdf_items(self, root: ET.Element) -> List[ET.Element]:
        items = root.findall("default:item", namespaces=self.NAMESPACES)

        if not items:
            # Fallback to non-namespaced search if nothing found
            items = root.findall(".//item")

        logger.debug(f"Found {len(items)} items in RDF format")
        return items

    def _create_document(self, item: ET.Element, config: Dict) -> Document:
        description = self._extract_description(item)

        return Document(
            **config.get("defaults", {}),
            title=self._extract_text(item, "title") or "No title",
            summary=description,
            publishedOn=self._parse_date(item),
            linkToRegChangeText=self._extract_link(item),
        )

    def _extract_text(self, item: ET.Element, tag: str) -> Optional[str]:
        # Try default namespace first
        elem = item.find(f"default:{tag}", namespaces=self.NAMESPACES)
        if elem is not None and elem.text:
            return elem.text.strip()

        # Try dc namespace for some fields
        if tag == "date":
            elem = item.find(f"dc:{tag}", namespaces=self.NAMESPACES)
            if elem is not None and elem.text:
                return elem.text.strip()

        # Fallback to direct tag search
        elem = item.find(tag)
        return elem.text.strip() if elem is not None and elem.text else None

    def _extract_description(self, item: ET.Element) -> str:
        description = self._extract_text(item, "description") or ""
        return " ".join(description.split())

    def _parse_date(self, item: ET.Element) -> Optional[str]:
        date_text = self._extract_text(item, "date")  # Looks for dc:date

        if not date_text:
            return None

        try:
            return datetime.datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%SZ").isoformat()
        except ValueError:
            return date_text  # Return raw string if parsing fails

    def _extract_link(self, item: ET.Element) -> str:
        link = self._extract_text(item, "link") or ""
        if not link:
            # Use rdf:about attribute if no link element found
            link = item.get(f"{{{self.NAMESPACES['rdf']}}}about", "")
        return link.strip()

    def _extract_source(self, item: ET.Element) -> Optional[str]:
        cb_news = item.find("cb:news", namespaces=self.NAMESPACES)
        if cb_news is None:
            return None

        inst_abbrev = cb_news.find("cb:institutionAbbrev", namespaces=self.NAMESPACES)
        return inst_abbrev.text if inst_abbrev is not None else None
