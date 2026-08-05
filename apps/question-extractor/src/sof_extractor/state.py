"""State passed between the first extraction graph's nodes."""

from __future__ import annotations

from typing import TypedDict

from .schemas import ExtractionResult


class ExtractionState(TypedDict, total=False):
    image_path: str
    model_name: str
    raw_model_response: str
    extraction: ExtractionResult
    markdown_content: str
    output_path: str
    errors: list[str]
