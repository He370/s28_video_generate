"""
graph.py — LangGraph StateGraph Definition

Defines the graph topology:
    __start__ → planner → generator → reviewer → (conditional edge)
                                                    ├─ __end__ (passed)
                                                    ├─ planner (retry)
                                                    └─ __end__ (max retries)
"""

import logging

from langgraph.graph import StateGraph, END

from langchain.music_video.state import VideoGenerationState
from langchain.music_video.nodes.planner import planner_node
from langchain.music_video.nodes.generator import generator_node
from langchain.music_video.nodes.reviewer import reviewer_node

logger = logging.getLogger(__name__)


def route_after_review(state: VideoGenerationState) -> str:
    """
    Conditional edge function: decide what happens after the reviewer.

    Returns:
        "__end__"   — if review passed OR max retries exceeded
        "planner"   — if review failed and retries remain
    """
    if state.get("review_passed"):
        logger.info("✅ Routing → END (review passed)")
        return END

    max_retries = state.get("max_retries", 2)
    retry_count = state.get("retry_count", 0)

    if retry_count >= max_retries:
        logger.error(f"❌ Routing → END (max retries {max_retries} exceeded)")
        return END

    logger.info(f"🔄 Routing → PLANNER (retry {retry_count + 1}/{max_retries})")
    return "planner"


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for music video generation.

    Returns:
        A compiled StateGraph ready to be invoked.
    """
    # Create the graph with our state schema
    graph = StateGraph(VideoGenerationState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("generator", generator_node)
    graph.add_node("reviewer", reviewer_node)

    # Set the entry point
    graph.set_entry_point("planner")

    # Add edges
    graph.add_edge("planner", "generator")      # planner → generator (always)
    graph.add_edge("generator", "reviewer")      # generator → reviewer (always)

    # Conditional edge after reviewer
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            END: END,
            "planner": "planner",
        },
    )

    # Compile the graph
    compiled = graph.compile()

    logger.info("LangGraph compiled successfully")
    logger.info(f"  Nodes: {list(compiled.get_graph().nodes)}")

    return compiled
