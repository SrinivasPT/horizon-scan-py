from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from src.agents.downloader import download_agent
from src.common.config import load_producer_config


class ProducerState(TypedDict):
    source_urls: List[str]
    batch_size: int
    current_batch: int
    raw_content: Dict[str, str]


def build_producer_pipeline():
    # config = load_producer_config(config_file)
    workflow = StateGraph(ProducerState)
    workflow.add_node("download", download_agent)
    workflow.set_entry_point("download")

    def should_continue(state):
        return (
            "download"
            if state["current_batch"] * state["batch_size"] < len(state["source_urls"])
            else END
        )

    workflow.add_conditional_edges("download", should_continue)
    return workflow.compile()
