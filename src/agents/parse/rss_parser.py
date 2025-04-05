import pprint
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from lxml import etree

from common.logging_config import get_logger
from model.document import Document

logger = get_logger(__name__, "DEBUG")


class RSSParser:
    """Simplified RSS parser supporting RDF, RSS, and Atom formats."""

    NAMESPACES = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "atom": "http://www.w3.org/2005/Atom",
        "default": "http://purl.org/rss/1.0/",
    }

    FEED_FORMATS = [
        {"name": "RDF", "root_tag": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF", "item_xpath": "//default:item"},
        {"name": "RSS", "root_tag": "rss", "item_xpath": "//channel/item"},
        {"name": "Atom", "root_tag": "{http://www.w3.org/2005/Atom}feed", "item_xpath": "//atom:entry"},
    ]

    def __init__(self):
        self._xpaths = {
            "title": ["title", "dc:title"],
            "description": ["description", "content:encoded"],
            "date": ["pubDate", "dc:date"],
            "link": ["link", "guid"],
            "category": ["category", "dc:subject"],  # Added XPaths for categories
        }

    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        """Parse RSS content into Document objects."""
        try:
            root = etree.fromstring(content.encode("utf-8"))
            items = self._extract_items(root)
            logger.debug(f"Extracted {len(items)} items from feed")

            documents = [self._create_document(item, config) for item in items]
            logger.debug(f"Parsed documents: {pprint.pprint(documents[5])}")

            return documents
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            return []

    def _extract_items(self, root: etree._Element) -> List[etree._Element]:
        """Extract items with basic format detection."""
        for fmt in self.FEED_FORMATS:
            if root.tag == fmt["root_tag"]:
                if items := root.xpath(fmt["item_xpath"], namespaces=self.NAMESPACES):
                    return items

        if items := root.xpath("//item | //entry"):
            return items

        return []

    def _create_document(self, item: etree._Element, config: Dict) -> Document:
        """Create document with essential fields only."""
        return Document(
            **config.get("defaults", {}),
            title=self._get_title(item, "title"),
            summary=self._get_description(item),
            publishedOn=self._get_date(item),
            linkToRegChangeText=self._get_link(item),
            category=self._get_category(item),
        )

    def _get_title(self, item: etree._Element, field: str) -> str:
        """Get text content from first matching XPath."""
        for xpath in self._xpaths.get(field, []):
            if result := item.xpath(xpath, namespaces=self.NAMESPACES):
                return (result[0].text or "").strip()
        return ""

    def _get_description(self, item: etree._Element) -> str:
        """Extract description using every possible method to ensure we get it"""
        # Try all possible ways to find a description, in order of likelihood
        extraction_methods = [
            lambda: item.find("description").text if item.find("description") is not None else None,
            lambda: item.xpath("string(.//description[1])"),
            lambda: item.xpath("string(.//*[local-name()='description'][1])"),
            lambda: item.xpath("string(.//content:encoded[1])", namespaces=self.NAMESPACES),
            lambda: item.xpath("string(.//dc:description[1])", namespaces=self.NAMESPACES),
        ]

        for method in extraction_methods:
            try:
                description = method()
                if description and str(description).strip():
                    return self._clean_html(str(description).strip())
            except Exception:
                continue

        return ""

    def _clean_html(self, text: str) -> str:
        """Convert HTML to plain text if needed."""
        if "<" in text and ">" in text:
            try:
                return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
            except Exception:
                return text
        return text

    def _get_date(self, item: etree._Element) -> Optional[str]:
        """Parse date with first matching format."""
        date_sources = [
            lambda: item.find("pubDate").text if item.find("pubDate") is not None else None,
            lambda: item.xpath("string(.//pubDate[1])"),
            lambda: item.xpath("string(.//dc:date[1])", namespaces=self.NAMESPACES),
        ]

        for source in date_sources:
            try:
                if date_str := source():
                    date_str = str(date_str).strip()
                    return date_str if date_str else None
            except Exception:
                continue

        return None

    def _get_link(self, item: etree._Element) -> str:
        """Robust link extraction with multiple fallback methods"""
        # Try all possible link locations in order of priority
        link_sources = [
            lambda: item.find("link").text if item.find("link") is not None else None,
            lambda: item.find("link").get("href") if item.find("link") is not None else None,
            lambda: item.find("guid").text if item.find("guid") is not None else None,
            lambda: item.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", ""),
            lambda: item.xpath("string(.//link[1]/@href | .//link[1]/text()"),
            lambda: item.xpath("string(.//guid[1]/text())"),
        ]

        for source in link_sources:
            try:
                if link := source():
                    if str(link).strip():
                        return str(link).strip()
            except Exception:
                continue

        return ""

    def _get_category(self, item: etree._Element) -> str:
        categories = set()  # Using a set to avoid duplicates

        # RSS 2.0: <category>Text</category>
        try:
            rss_cats = item.xpath(".//category/text()", namespaces=self.NAMESPACES)
            categories.update(cat.strip() for cat in rss_cats if cat and cat.strip())
        except Exception as e:
            logger.debug(f"Failed to extract RSS categories: {e}")

        # Atom: <category term="Technology"/>
        try:
            atom_cats = item.xpath(".//atom:category/@term", namespaces=self.NAMESPACES)
            categories.update(cat.strip() for cat in atom_cats if cat and cat.strip())
        except Exception as e:
            logger.debug(f"Failed to extract Atom categories: {e}")

        # Dublin Core: <dc:subject>Finance</dc:subject>
        try:
            dc_cats = item.xpath(".//dc:subject/text()", namespaces=self.NAMESPACES)
            categories.update(cat.strip() for cat in dc_cats if cat and cat.strip())
        except Exception as e:
            logger.debug(f"Failed to extract Dublin Core subjects: {e}")

        return ", ".join(sorted(categories)) if categories else ""
