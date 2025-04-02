import datetime
import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, List

from bs4 import BeautifulSoup

from agents.parse.base_parser import BaseParser
from model.document import Document

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSParser(BaseParser):
    """Enhanced RSS parser with better format handling"""

    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        try:
            root = ET.fromstring(content)
            documents = []
            namespaces = {
                "atom": "http://www.w3.org/2005/Atom",
                "dc": "http://purl.org/dc/elements/1.1/",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            }

            # Flexible item detection
            items = (
                root.findall(".//item")
                or root.findall(".//rdf:item", namespaces)
                or root.findall(".//atom:entry", namespaces)
            )

            for item in items:
                doc = Document(**self.defaults)

                doc.title = item.findtext("title") or item.findtext("atom:title", namespaces) or "No title"

                # Enhanced description handling
                desc_elem = item.find("description") or item.find("atom:summary", namespaces)
                if desc_elem is not None:
                    description = desc_elem.text or ""
                    if re.search(r"<[^>]+>", description):
                        doc.htmlContent = description
                        soup = BeautifulSoup(description, "html.parser")
                        doc.summary = soup.get_text(strip=True)
                    else:
                        doc.summary = description

                # Robust date handling
                date_str = (
                    item.findtext("pubDate")
                    or item.findtext("dc:date", namespaces)
                    or item.findtext("atom:published", namespaces)
                )
                if date_str:
                    try:
                        doc.publishedOn = datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z").isoformat()
                    except ValueError:
                        doc.publishedOn = date_str

                # Link handling
                link_elem = item.find("link") or item.find("atom:link", namespaces)
                if link_elem is not None:
                    doc.linkToRegChangeText = link_elem.text or link_elem.get("href")

                doc = await self.process_dynamic_defaults(doc)
                documents.append(doc)

            logger.info(f"Parsed {len(documents)} RSS items")
            return documents
        except Exception as e:
            logger.error(f"Error parsing RSS: {str(e)}")
            return []
