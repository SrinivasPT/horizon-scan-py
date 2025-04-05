import pprint
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from lxml import etree

from common.logging_config import get_logger
from model.document import Document

logger = get_logger(__name__, "DEBUG")


class RSSParser:
    """Universal RSS parser using lxml that handles both RDF and standard RSS formats."""

    # Define namespace mappings for different feed types
    NAMESPACES = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "cb": "http://www.cbwiki.net/wiki/index.php/Specification_1.1",
        "atom": "http://www.w3.org/2005/Atom",
        "default": "http://purl.org/rss/1.0/",  # For RDF feeds
        "media": "http://search.yahoo.com/mrss/",
        "gd": "http://base.google.com/ns/1.0",
    }

    def __init__(self):
        # Precompile XPath expressions for better performance
        self._xpaths = {
            "rdf_items": "//default:item",
            "rss_items": "//channel/item",
            "atom_entries": "//atom:entry",
            "title": ["title", "dc:title", "media:title"],
            "description": ["description", "content:encoded", "dc:description"],
            "date": ["pubDate", "published", "dc:date", "updated"],
            "link": ["link", "atom:link/@href", "guid"],
            "cb_source": "cb:news/cb:institutionAbbrev",
        }

    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        """Parse RSS content into Document objects."""
        logger.info(f"Parsing RSS content for {config['source']}")

        try:
            root = self._parse_xml(content)
            items = self._extract_items(root)
            documents = [self._create_document(item, config) for item in items]

            logger.info(f"Successfully parsed {len(documents)} items")
            logger.debug(f"Parsed documents: {pprint.pprint(documents)}")
            return documents

        except etree.XMLSyntaxError as e:
            logger.error(f"XML parsing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing RSS: {str(e)}", exc_info=True)
        return []

    def _parse_xml(self, content: str) -> etree._Element:
        """Parse XML content with lxml, handling encoding issues."""
        try:
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            return etree.fromstring(content.encode("utf-8"), parser=parser)
        except ValueError:
            # Fallback if content is already bytes
            return etree.fromstring(content, parser=parser)

    def _extract_items(self, root: etree._Element) -> List[etree._Element]:
        """Extract items based on feed format detection."""
        # Check for RDF format (BIS)
        if root.tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF":
            items = root.xpath(self._xpaths["rdf_items"], namespaces=self.NAMESPACES)
            if items:
                logger.debug("Detected RDF format")
                return items

        # Check for standard RSS 2.0 (FDIC)
        if root.tag == "rss":
            items = root.xpath(self._xpaths["rss_items"], namespaces=self.NAMESPACES)
            if items:
                logger.debug("Detected RSS 2.0 format")
                return items

        # Check for Atom format
        if root.tag == "{http://www.w3.org/2005/Atom}feed":
            items = root.xpath(self._xpaths["atom_entries"], namespaces=self.NAMESPACES)
            if items:
                logger.debug("Detected Atom format")
                return items

        # Fallback: try to find items anywhere
        logger.warning("Unknown feed format, attempting fallback item extraction")
        return root.xpath("//item | //entry")

    def _create_document(self, item: etree._Element, config: Dict) -> Document:
        """Create a Document from an RSS item."""
        description, html_content = self._extract_description(item)

        return Document(
            **config.get("defaults", {}),
            title=self._extract_title(item),
            summary=description,
            publishedOn=self._parse_date(item),
            linkToRegChangeText=self._extract_link(item),
        )

    def _extract_title(self, item: etree._Element) -> str:
        """Extract title from multiple possible locations."""
        for xpath in self._xpaths["title"]:
            result = item.xpath(xpath, namespaces=self.NAMESPACES)
            if result and result[0].text and result[0].text.strip():
                return result[0].text.strip()
        return "No title"

    def _extract_description(self, item: etree._Element) -> Tuple[str, str]:
        """Extract both plain text and HTML versions of description."""
        description = ""

        # Try different description fields
        for xpath in self._xpaths["description"]:
            result = item.xpath(xpath, namespaces=self.NAMESPACES)
            if result and result[0].text and result[0].text.strip():
                description = result[0].text.strip()
                break

        # Process HTML content if present
        if "<" in description and ">":
            try:
                soup = BeautifulSoup(description, "html.parser")
                plain_text = soup.get_text(" ", strip=True)
                # Clean up excessive whitespace
                plain_text = " ".join(plain_text.split())
                return plain_text, description
            except Exception as e:
                logger.warning(f"Failed to parse HTML description: {str(e)}")
                return description, ""

        return description, ""

    def _parse_date(self, item: etree._Element) -> Optional[str]:
        """Parse date from various possible fields and formats."""
        date_text = ""

        # Try different date fields
        for xpath in self._xpaths["date"]:
            result = item.xpath(xpath, namespaces=self.NAMESPACES)
            if result and result[0].text and result[0].text.strip():
                date_text = result[0].text.strip()
                break

        if not date_text:
            return None

        # Try common date formats
        date_formats = [
            "%Y-%m-%dT%H:%M:%SZ",  # ISO format (BIS)
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 822 (FDIC)
            "%a, %d %b %Y %H:%M:%S %Z",  # With timezone name
            "%Y-%m-%d %H:%M:%S",  # Simple datetime
            "%Y-%m-%d",  # Simple date
            "%d %b %Y",  # FDIC publication date
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_text, fmt).isoformat()
            except ValueError:
                continue

        return date_text  # Return raw string if parsing fails

    def _extract_link(self, item: etree._Element) -> str:
        """Extract link with multiple fallback options."""
        # Try different link fields
        for xpath in self._xpaths["link"]:
            result = item.xpath(xpath, namespaces=self.NAMESPACES)
            if result:
                if isinstance(result[0], str):
                    return result[0].strip()
                if result[0].text and result[0].text.strip():
                    return result[0].text.strip()
                if xpath == "atom:link/@href":
                    return result[0].strip()

        # Try RDF about attribute
        about = item.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
        if about:
            return about.strip()

        return ""

    def _extract_source(self, item: etree._Element) -> Optional[str]:
        """Extract source from cb:news if available (BIS specific)."""
        result = item.xpath(self._xpaths["cb_source"], namespaces=self.NAMESPACES)
        if result and result[0].text and result[0].text.strip():
            return result[0].text.strip()
        return None
