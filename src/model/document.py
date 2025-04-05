from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Document:
    source: Optional[str] = None
    typeOfChange: Optional[str] = None
    eventType: Optional[str] = None
    category: Optional[str] = None  # Custom field for categorizing documents
    issuingAuthority: Optional[str] = None
    identifier: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    linkToRegChangeText: Optional[str] = None
    publishedOn: Optional[str] = None
    htmlContent: Optional[str] = None
    pdfContent: Optional[str] = None
    introducedOn: Optional[str] = None
    citationId: Optional[str] = None
    billType: Optional[str] = None
    regType: Optional[str] = None
    year: Optional[str] = None
    regulationStatus: Optional[str] = None
    billStatus: Optional[str] = None
    firstEffectiveDate: Optional[str] = None
    comments: Optional[str] = None
    enactedDate: Optional[str] = None
    topic: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}
