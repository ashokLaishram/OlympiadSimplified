"""The first, intentionally small LangGraph extraction workflow."""

from __future__ import annotations

from pathlib import Path

from langgraph.graph import END, START, StateGraph

from .extractor import invoke_extractor, invoke_json_repair, parse_extraction
from .markdown import render_markdown
from .state import ExtractionState


def extract_questions(state: ExtractionState) -> ExtractionState:
    raw = invoke_extractor(state["image_path"], state["model_name"])
    return {"raw_model_response": raw, "errors": state.get("errors", [])}


def validate_or_repair(state: ExtractionState) -> ExtractionState:
    source_file = Path(state["image_path"]).name
    try:
        extraction = parse_extraction(state["raw_model_response"], source_file)
        return {"extraction": extraction, "errors": state.get("errors", [])}
    except Exception as first_error:
        repaired = invoke_json_repair(state["raw_model_response"], state["model_name"])
        try:
            extraction = parse_extraction(repaired, source_file)
        except Exception as repair_error:
            message = (
                "Gemma did not return valid extraction JSON after one repair attempt. "
                f"First error: {first_error}. Repair error: {repair_error}"
            )
            raise ValueError(message) from repair_error
        return {
            "extraction": extraction,
            "raw_model_response": repaired,
            "errors": [*state.get("errors", []), f"Initial JSON was repaired: {first_error}"],
        }


def render_output(state: ExtractionState) -> ExtractionState:
    return {"markdown_content": render_markdown(state["extraction"]), "errors": state.get("errors", [])}


def build_graph():
    graph = StateGraph(ExtractionState)
    graph.add_node("extract_questions", extract_questions)
    graph.add_node("validate_or_repair", validate_or_repair)
    graph.add_node("render_output", render_output)
    graph.add_edge(START, "extract_questions")
    graph.add_edge("extract_questions", "validate_or_repair")
    graph.add_edge("validate_or_repair", "render_output")
    graph.add_edge("render_output", END)
    return graph.compile()
