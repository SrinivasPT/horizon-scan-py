from langgraph.graph import END, StateGraph

from agents.classify import classifier
from agents.downloader import download_agent
from agents.parse import parser_cleaner
from agents.parse.parser_agent import ParserAgent
from agents.persist import persister
from model.state import State


def build_producer_pipeline():
    agent_map = {
        "parser": parser_cleaner,
        "persist": persister,
        "classify": classifier,
    }
    parser_agent = ParserAgent()

    # Define workflow
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("download", download_agent)
    workflow.add_node("parse", parser_agent.parse_content)

    # Set entry point
    workflow.set_entry_point("download")

    # Define flow
    workflow.add_edge("download", "parse")

    # Conditional continuation for download batches
    def should_continue(state):
        return "download" if state["current_batch"] * state["batch_size"] < len(state["source_urls"]) else END

    workflow.add_conditional_edges("download", should_continue)

    # Compile the workflow
    return workflow.compile()
