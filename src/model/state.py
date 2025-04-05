from typing import Annotated, Dict, List, Literal, TypedDict

from model.document import Document


class ColumnConfig(TypedDict, total=False):
    name: str
    selector: str
    isLink: bool


class ParserConfig(TypedDict, total=False):
    parser: Literal["HTML-PARSER", "RSS-PARSER"]  # Now matches the keys in ParserAgent
    tableSelector: str  # Only used for HTML-PARSER
    columns: List[ColumnConfig]  # Only used for HTML-PARSER


class ScanConfigItem(TypedDict):
    source: str
    title: str
    url: str
    parser_config: ParserConfig
    defaults: Dict[str, str]


def add_documents(current: List[Document], updated: List[Document]) -> List[Document]:
    result = current.copy()

    for new_doc in updated:
        if not any(
            doc["source"] == new_doc["source"]
            and doc["title"] == new_doc["title"]
            and doc["publishedOn"] == new_doc["publishedOn"]
            for doc in result
        ):
            result.append(new_doc)

    return result


class State(TypedDict):
    scan_config: List[ScanConfigItem]
    batch_size: int
    current_batch: int
    raw_content: Dict[str, str]
    documents: Annotated[List[Document], add_documents]
