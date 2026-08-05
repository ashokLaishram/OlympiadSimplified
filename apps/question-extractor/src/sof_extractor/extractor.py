"""Ollama image prompting and robust parsing of extraction output."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from PIL import Image, UnidentifiedImageError

from .schemas import ExtractionResult

EXTRACTION_PROMPT = """You are transcribing a SOF Olympiad question page.
Read every visible multiple-choice question in the supplied PNG. Do not solve any question.

Return ONLY one JSON object, without Markdown fences or commentary, matching exactly:
{
  "source_file": "original filename",
  "questions": [
    {
      "number": "1",
      "text": "question text only",
      "options": [{"label": "A", "text": "option text"}],
      "image_description": null,
      "uncertain_text": []
    }
  ]
}

Rules:
- Preserve question order, option labels, mathematical symbols, and wording as faithfully as possible.
- Do not invent missing text or an answer. Put unreadable fragments in uncertain_text.
- Put diagrams, tables, or figures required to understand a question in image_description.
- Exclude page headers, branding, marks, and instructions unless they are part of a question.
- If no questions are visible, return an empty questions list.
"""

REPAIR_PROMPT = """Convert the following attempted SOF question extraction into valid JSON only.
Do not add facts, solve questions, or remove uncertainty. The required schema is:
{"source_file": "string", "questions": [{"number": "string", "text": "string", "options": [{"label": "string", "text": "string"}], "image_description": "string or null", "uncertain_text": ["string"]}]}

Attempted extraction:
"""


def validate_png(image_path: str) -> Path:
    """Ensure a path is a readable PNG before passing it to the model."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file was not found: {path}")
    if path.suffix.lower() != ".png":
        raise ValueError(f"Only PNG input is supported in v1, received: {path.suffix or 'no extension'}")
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                raise ValueError(f"Input is not a PNG image: {path}")
            image.verify()
    except UnidentifiedImageError as exc:
        raise ValueError(f"Input is not a readable image: {path}") from exc
    return path


def _message_content(image_path: Path, prompt: str) -> list[dict[str, object]]:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
    ]


def invoke_extractor(image_path: str, model_name: str) -> str:
    """Ask the local vision model to extract questions from a verified PNG."""
    path = validate_png(image_path)
    model = ChatOllama(model=model_name, temperature=0)
    response = model.invoke(HumanMessage(content=_message_content(path, EXTRACTION_PROMPT)))
    return _as_text(response.content)


def invoke_json_repair(raw_response: str, model_name: str) -> str:
    """Use one bounded repair attempt for non-JSON model responses."""
    model = ChatOllama(model=model_name, temperature=0)
    response = model.invoke(REPAIR_PROMPT + raw_response)
    return _as_text(response.content)


def parse_extraction(raw_response: str, source_file: str) -> ExtractionResult:
    """Parse direct JSON or JSON wrapped in a Markdown code fence."""
    candidate = _json_candidate(raw_response)
    payload = json.loads(candidate)
    if not payload.get("source_file"):
        payload["source_file"] = source_file
    return ExtractionResult.model_validate(payload)


def _as_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                pieces.append(item["text"])
            elif isinstance(item, str):
                pieces.append(item)
        return "\n".join(pieces)
    return str(content)


def _json_candidate(raw_response: str) -> str:
    stripped = raw_response.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    start, end = stripped.find("{"), stripped.rfind("}")
    return stripped[start : end + 1] if start >= 0 and end > start else stripped
