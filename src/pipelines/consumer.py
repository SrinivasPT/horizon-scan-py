from typing import Dict, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.classify import classifier
from src.agents.fetch import fetch_raw_content
from src.agents.parse import parser_cleaner
from src.agents.persist import persister
from src.common.config import load_config


class ConsumerState(TypedDict):
    raw_content: Dict[str, str]
    cleaned_data: Dict[str, dict]
    stored_data: Dict[str, dict]
    classified_data: Dict[str, str]


def build_consumer_pipeline(config_file):
    config = load_config(config_file)
    workflow = StateGraph(ConsumerState)

    agent_map = {
        "fetch": fetch_raw_content,
        "parse_clean": parser_cleaner,
        "persist": persister,
        "classify": classifier,
    }

    prev_node = None
    for agent in config["agents"]:
        if agent["enabled"]:
            workflow.add_node(agent["name"], agent_map[agent["name"]])
            if prev_node:
                workflow.add_edge(prev_node, agent["name"])
            else:
                workflow.set_entry_point(agent["name"])
            prev_node = agent["name"]

    def should_continue(state):
        return "fetch" if fetch_unprocessed(limit=1) else END

    if prev_node:
        workflow.add_conditional_edges(prev_node, should_continue)

    return workflow.compile()
