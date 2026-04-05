"""
graph.py — LangGraph StateGraph Definition for Long2Shorts

Defines the graph topology:
    __start__ → director → veo_generator → audio_agent → assembler → __end__

Simple sequential pipeline — no conditional routing needed.
"""

import logging

from langgraph.graph import StateGraph, END

from langchain.long2shorts.state import VideoState
from langchain.long2shorts.nodes.director import director_node
from langchain.long2shorts.nodes.veo_generator import veo_generator_node
from langchain.long2shorts.nodes.audio_agent import audio_agent_node
from langchain.long2shorts.nodes.assembler import assembler_node

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for Long2Shorts conversion.

    Pipeline:
        Director → Veo Generator → Audio Agent → Assembler → END

    Returns:
        A compiled StateGraph ready to be invoked.
    """
    # Create the graph with our state schema
    graph = StateGraph(VideoState)

    # Add nodes
    graph.add_node("director", director_node)
    graph.add_node("veo_generator", veo_generator_node)
    graph.add_node("audio_agent", audio_agent_node)
    graph.add_node("assembler", assembler_node)

    # Set the entry point
    graph.set_entry_point("director")

    # Add sequential edges
    graph.add_edge("director", "veo_generator")       # Director → Veo Generator
    graph.add_edge("veo_generator", "audio_agent")     # Veo Generator → Audio Agent
    graph.add_edge("audio_agent", "assembler")         # Audio Agent → Assembler
    graph.add_edge("assembler", END)                   # Assembler → END

    # Compile the graph
    compiled = graph.compile()

    logger.info("LangGraph Long2Shorts compiled successfully")
    logger.info(f"  Nodes: {list(compiled.get_graph().nodes)}")

    return compiled
