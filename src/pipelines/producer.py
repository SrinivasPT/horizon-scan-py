from typing import Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.classify import classifier
from src.agents.downloader import download_agent
from src.agents.fetch import fetch_raw_content
from src.agents.parse import parser_cleaner
from src.agents.persist import persister


class ProducerState(TypedDict):
    source_urls: List[str]
    batch_size: int
    current_batch: int
    raw_content: Dict[str, str]


def build_producer_pipeline():
    agent_map = {
        "fetch": fetch_raw_content,
        "parse_clean": parser_cleaner,
        "persist": persister,
        "classify": classifier,
    }

    workflow = StateGraph(ProducerState)

    workflow.add_node("download", download_agent)
    workflow.set_entry_point("download")

    def should_continue(state):
        return "download" if state["current_batch"] * state["batch_size"] < len(state["source_urls"]) else END

    workflow.add_conditional_edges("download", should_continue)
    return workflow.compile()
