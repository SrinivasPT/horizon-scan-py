import json
import logging
import pprint
from typing import Dict, List, Optional

from agents.parse.base_parser import BaseParser
from model.document import Document

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FedRegisterParser(BaseParser):
    def __init__(self):
        pass

    async def parse(self, content: str, config: Dict, base_url: str = None) -> List[Document]:  # noqa: ARG002
        logger.info("Starting Federal Register Parser")
        try:
            # Parse the JSON content string
            data = json.loads(content)
            logger.debug(f"Federal Register JSON content parsed, found {data.get('count', 0)} documents")

            # Check if we have results
            if not data.get("results") or not isinstance(data["results"], list):
                logger.warn("No results found in Federal Register JSON content")
                return []

            # Map API results to Document objects
            documents = [self._map_fed_register_item_to_document(item, config) for item in data["results"]]

            if documents and len(documents) > 0:
                logger.debug(f"Sample document: {pprint.pformat(documents[0].__dict__)}")

            logger.info(f"Total documents: {len(documents)}")
            return documents
        except Exception as e:
            logger.error(f"Error parsing Federal Register API: {str(e)}")
            return []

    def _map_fed_register_item_to_document(self, item: Dict, config: Dict) -> Document:
        """Map a Federal Register API result to a Document object."""
        doc = Document(**config.get("defaults", {}))

        # Basic Document fields
        doc.title = item.get("title", "No title")
        doc.summary = item.get("abstract", "")
        doc.publishedOn = self._parse_date(item.get("publication_date") or item.get("filed_at"))
        doc.linkToRegChangeText = item.get("pdf_url", "")

        # Additional Federal Register specific fields
        doc.introducedOn = item.get("effective_on")
        doc.firstEffectiveDate = item.get("effective_on")
        doc.enactedDate = item.get("enacted_on")
        doc.identifier = item.get("document_number")
        doc.regType = item.get("type")
        doc.citationId = item.get("citation")

        # Handle agencies
        agencies = item.get("agencies", [])
        if agencies and len(agencies) > 0:
            doc.issuingAuthority = agencies[0].get("name", "")

            # Extract agency slugs for source field
            agency_slugs = [agency.get("slug", "") for agency in agencies if agency.get("slug")]
            if agency_slugs:
                doc.source = ", ".join(agency_slugs)

        return doc

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to standard format or return None if invalid."""
        if not date_str:
            return None

        try:
            # Assuming date_str is in YYYY-MM-DD format
            return date_str
        except Exception as e:
            logger.warning(f"Failed to parse date: {date_str}, error: {str(e)}")
            return None

    async def close(self):
        await super().close()
        # Close any resources if needed
