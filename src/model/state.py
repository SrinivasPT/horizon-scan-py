from typing import Dict, List, Literal, TypedDict


class ColumnConfig(TypedDict, total=False):
    name: str
    selector: str
    isLink: bool


class ParserConfig(TypedDict, total=False):
    parser: Literal["HTML-PARSER", "RSS-PARSER"]
    tableSelector: str  # Only used for HTML-PARSER
    columns: List[ColumnConfig]  # Only used for HTML-PARSER


class ScanConfigItem(TypedDict):
    source: str
    title: str
    url: str
    parser_config: ParserConfig
    defaults: Dict[str, str]


class State(TypedDict):
    scan_config: List[ScanConfigItem]
    batch_size: int
    current_batch: int
    raw_content: Dict[str, str]
    download_status: Dict[str, str]
