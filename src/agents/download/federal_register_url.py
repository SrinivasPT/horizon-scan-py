import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlencode

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.federalregister.gov/api/v1/documents.json"
AGENCIES_PER_REQUEST = 20

# List of agency identifiers of interest
INTERESTED_AGENCIES = [
    "agriculture-department",
    "alcohol-and-tobacco-tax-and-trade-bureau",
    "census-bureau",
    "commerce-department",
    "commodity-credit-corporation",
    "commodity-futures-trading-commission",
    "community-development-financial-institutions-fund",
    "comptroller-of-the-currency",
    "consumer-financial-protection-bureau",
    "defense-department",
    "economic-analysis-bureau",
    # "education-department",
    # "employee-benefits-security-administration",
    # "employment-and-training-administration",
    # "employment-standards-administration",
    # "equal-employment-opportunity-commission",
    # "executive-office-of-the-president",
    # "farm-credit-administration",
    # "farm-credit-system-insurance-corporation",
    # "farm-service-agency",
    # "federal-accounting-standards-advisory-board",
    # "federal-aviation-administration",
    # "federal-communications-commission",
    # "federal-contract-compliance-programs-office",
    # "federal-crop-insurance-corporation",
    # "federal-deposit-insurance-corporation",
    # "federal-election-commission",
    # "federal-emergency-management-agency",
    # "federal-energy-regulatory-commission",
    # "federal-financial-institutions-examination-council",
    # "federal-housing-finance-agency",
    # "federal-housing-finance-board",
    # "federal-labor-relations-authority",
    # "federal-reserve-system",
    # "federal-trade-commission",
    # "financial-crimes-enforcement-network",
    # "financial-stability-oversight-council",
    # "foreign-assets-control-office",
    # "health-and-human-services-department",
    # "homeland-security-department",
    # "housing-and-urban-development-department",
    # "industry-and-security-bureau",
    # "internal-revenue-service",
    # "judicial-conference-of-the-united-states",
    # "justice-department",
    # "labor-department",
    # "national-archives-and-records-administration",
    # "national-credit-union-administration",
    # "national-labor-relations-board",
    # "occupational-safety-and-health-administration",
    # "patent-and-trademark-office",
    # "pension-benefit-guaranty-corporation",
    # "personnel-management-office",
    # "postal-regulatory-commission",
    # "postal-service",
    # "rural-business-cooperative-service",
    # "rural-housing-service",
    # "rural-utilities-service",
    # "securities-and-exchange-commission",
    # "small-business-administration",
    # "social-security-administration",
    # "state-department",
    # "treasury-department",
    # "united-states-sentencing-commission",
    # "wage-and-hour-division",
]

# List of search terms of interest
INTERESTED_TERMS = []


def chunk_agencies(agencies: List[str], chunk_size: int) -> List[List[str]]:
    """Split the list of agencies into smaller chunks."""
    return [agencies[i : i + chunk_size] for i in range(0, len(agencies), chunk_size)]


def build_fed_register_url(date_str: Optional[str] = None, agencies: List[str] = None, terms: List[str] = None) -> str:
    """Build the URL for the Federal Register API with query parameters."""

    params = {
        "conditions[publication_date][is]": date_str,
    }

    # Add agency conditions for this chunk
    for agency in agencies:
        params.setdefault("conditions[agencies][]", []).append(agency)

    # Add term conditions
    for term in terms:
        params.setdefault("conditions[type][]", []).append(term)

    # Convert the params dictionary to a URL query string
    query_string = urlencode(params, doseq=True)
    return f"{BASE_URL}?{query_string}"


def get_federal_register_urls() -> List[str]:
    # Use current date
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Split agencies into chunks to avoid URL length limits
    agency_chunks = chunk_agencies(INTERESTED_AGENCIES, AGENCIES_PER_REQUEST)
    logger.info(f"Split {len(INTERESTED_AGENCIES)} agencies into {len(agency_chunks)} chunks")

    urls = []
    for i, agency_chunk in enumerate(agency_chunks):
        logger.info(f"Creating URL for agency chunk {i+1} of {len(agency_chunks)}")
        url = build_fed_register_url(date_str, agency_chunk, INTERESTED_TERMS)
        logger.debug(f"Federal Register URL for chunk {i+1}: {url}")
        urls.append(url)

    return urls
