import pprint
from datetime import datetime
from typing import Any, Dict, List

import feedparser
from bs4 import BeautifulSoup

from agents.parse.base_parser import BaseParser
from common.logging_config import get_logger
from model.document import Document

logger = get_logger(__name__, "DEBUG")


class RssParser(BaseParser):
    def __init__(self):
        pass

    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        try:
            feed = feedparser.parse(content)
            documents = []

            for entry in feed.entries:
                # Extract data from entry
                data = self._extract_entry_data(entry, feed, base_url)

                # Create document with extracted data and config defaults
                document = Document(
                    **config.get("defaults", {}),
                    title=data.get("title", ""),
                    summary=data.get("summary", ""),
                    publishedOn=data.get("publishedOn", ""),
                    linkToRegChangeText=data.get("link", ""),
                    category=data.get("category", ""),
                )
                documents.append(document)

            logger.debug(f"Parsed documents: {pprint.pprint(documents[5])}")
            logger.debug(f"Parsed {len(documents)} documents from feed at {base_url}")
            return documents
        except Exception as e:
            logger.error(f"Error parsing feed content: {str(e)}")
            return []

    def _extract_entry_data(self, entry: Any, feed: Any, base_url: str) -> Dict[str, Any]:
        data = {
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "publishedOn": entry.get("published", ""),
            "link": entry.get("link", ""),
            "category": self._extract_category(entry),
            "source": feed.feed.get("title", "") or base_url,
        }

        # If summary is empty, try to get description
        if not data["summary"] and "description" in entry:
            data["summary"] = entry.description

        # Clean HTML tags from summary
        data["summary"] = self._clean_html(data["summary"])

        # Convert published date if available
        if "published_parsed" in entry and entry.published_parsed:
            try:
                data["publishedOn"] = datetime(*entry.published_parsed[:6]).isoformat()
            except (TypeError, ValueError) as e:
                logger.debug(f"Failed to parse date: {e}")

        return data

    def _clean_html(self, text: str) -> str:
        if not text:
            return ""

        if "<" in text and ">" in text:
            try:
                return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
            except Exception:
                return text
        return text

    def _extract_category(self, entry: Any) -> str:
        categories = set()

        # Extract categories from tags list
        if hasattr(entry, "tags") and entry.tags:
            for tag in entry.tags:
                if hasattr(tag, "term") and tag.term:
                    categories.add(tag.term.strip())

        # Extract categories from category field
        if hasattr(entry, "category") and entry.category:
            categories.add(entry.category.strip())

        return ", ".join(sorted(categories)) if categories else ""
