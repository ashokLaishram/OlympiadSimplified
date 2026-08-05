"""Deterministic rendering; the model never formats final Markdown."""

from __future__ import annotations

from .schemas import ExtractionResult


def render_markdown(extraction: ExtractionResult) -> str:
    lines = ["# Extracted SOF Questions", "", f"_Source: {extraction.source_file}_", ""]
    if not extraction.questions:
        lines.extend(["No questions were detected.", ""])
    for question in extraction.questions:
        lines.extend([f"## Question {question.number}", "", question.text, ""])
        for option in question.options:
            lines.append(f"- {option.label}. {option.text}")
        if question.options:
            lines.append("")
        if question.image_description:
            lines.extend([f"> Figure/table: {question.image_description}", ""])
        if question.uncertain_text:
            lines.extend(["> Extraction uncertainties:", *[f"> - {text}" for text in question.uncertain_text], ""])
    return "\n".join(lines).rstrip() + "\n"
