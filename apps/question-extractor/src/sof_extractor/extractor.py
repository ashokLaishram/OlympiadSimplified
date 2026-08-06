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

EXTRACTION_PROMPT = """You are transcribing and synthesizing a SOF Olympiad question page.
Read every visible multiple-choice question in the supplied image. Do not solve any question.

Return ONLY one JSON object, without Markdown fences or commentary, matching exactly the schema below:
{
  "source_file": "original filename",
  "questions": [
    {
      "number": "1",
      "text": "question text only",
      "options": [{"label": "A", "text": "option text or visual description"}],
      "image_description": "short label or description of any figure",
      "visual_description": "detailed breakdown of illustrations, counting objects, abacus beads, shapes, colors, or coordinate markers",
      "unified_description": "a cohesive natural language description combining text query and visual elements into a single scene description",
      "roblox_scene": {
        "environment_theme": "Garden / Classroom / Forest / etc.",
        "interactive_elements": ["list of assets or interactive objects"],
        "visual_objects": [{"name": "butterfly", "quantity": 8, "color": "yellow", "spatial_layout": "flying in garden"}]
      },
      "uncertain_text": []
    }
  ]
}

Rules:
- Preserve question order, option labels, and wording as faithfully as possible.
- If options A, B, C, or D are images or diagrams, write a clear visual description of each diagram in the option's 'text' field (e.g., "Abacus showing 3 tens and 5 ones").
- In 'visual_description', accurately count items, describe shapes/colors, and note their layouts.
- In 'unified_description', synthesize the text query and visual elements into a single scene description for Roblox.
- If no questions are visible, return an empty questions list.
"""

REPAIR_PROMPT = """Convert the following attempted SOF question extraction into valid JSON only.
Do not add facts, solve questions, or remove uncertainty. The required schema is:
{"source_file": "string", "questions": [{"number": "string", "text": "string", "options": [{"label": "string", "text": "string"}], "image_description": "string or null", "visual_description": "string or null", "unified_description": "string", "roblox_scene": {"environment_theme": "string", "interactive_elements": ["string"], "visual_objects": [{"name": "string", "quantity": 0, "color": "string or null", "spatial_layout": "string or null"}]} or null, "uncertain_text": ["string"]}]}

Attempted extraction:
"""


def validate_image(image_path: str) -> Path:
    """Ensure a path is a readable PNG or JPEG before passing it to the model."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file was not found: {path}")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise ValueError(f"Only PNG and JPEG input are supported, received: {path.suffix or 'no extension'}")
    try:
        with Image.open(path) as image:
            if image.format not in {"PNG", "JPEG"}:
                raise ValueError(f"Input is not a PNG or JPEG image: {path}")
            image.verify()
    except UnidentifiedImageError as exc:
        raise ValueError(f"Input is not a readable image: {path}") from exc
    return path


def _message_content(image_path: Path, prompt: str) -> list[dict[str, object]]:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    return [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
    ]


def _split_landscape_image(image_path: Path) -> tuple[Path, Path]:
    """Splits a landscape image vertically down the center and returns paths to left and right halves."""
    temp_dir = Path("output") / ".tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    with Image.open(image_path) as img:
        width, height = img.size
        left_box = (0, 0, width // 2, height)
        right_box = (width // 2, 0, width, height)
        
        left_img = img.crop(left_box)
        right_img = img.crop(right_box)
        
        left_path = temp_dir / f"{image_path.stem}_left{image_path.suffix}"
        right_path = temp_dir / f"{image_path.stem}_right{image_path.suffix}"
        
        left_img.save(left_path, format=img.format)
        right_img.save(right_path, format=img.format)
        
        return left_path, right_path


def _extract_and_parse_single_image(path: Path, model: ChatOllama, model_name: str, original_filename: str) -> ExtractionResult:
    """Invokes VLM on a single image and parses/repairs the JSON response."""
    response = model.invoke([HumanMessage(content=_message_content(path, EXTRACTION_PROMPT))])
    raw_text = _as_text(response.content)
    try:
        return parse_extraction(raw_text, original_filename)
    except Exception as first_error:
        # Write to debug file
        debug_dir = Path("output")
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / f"debug_raw_{path.stem}.txt").write_text(raw_text, encoding="utf-8")
        print(f"--- DEBUG: First parse failed for {path.name}. Raw response saved to debug_raw_{path.stem}.txt. Error: {first_error} ---")
        repaired = invoke_json_repair(raw_text, model_name)
        (debug_dir / f"debug_repaired_{path.stem}.txt").write_text(repaired, encoding="utf-8")
        try:
            return parse_extraction(repaired, original_filename)
        except Exception as repair_error:
            print(f"--- DEBUG: Repair parse failed for {path.name}. Repaired response saved to debug_repaired_{path.stem}.txt. Error: {repair_error} ---")
            raise ValueError(
                f"Failed to parse and repair JSON for {path.name}. "
                f"First error: {first_error}. Repair error: {repair_error}"
            ) from repair_error


def invoke_extractor(image_path: str, model_name: str) -> str:
    """Ask the local vision model to extract questions from a verified PNG or JPEG, splitting landscape images if needed."""
    path = validate_image(image_path)
    model = ChatOllama(model=model_name, temperature=0, num_predict=4096, num_ctx=8192)
    
    with Image.open(path) as img:
        width, height = img.size
        is_landscape = (width / height) > 1.25
        
    if not is_landscape:
        response = model.invoke([HumanMessage(content=_message_content(path, EXTRACTION_PROMPT))])
        return _as_text(response.content)
        
    # Split the landscape image
    left_path, right_path = _split_landscape_image(path)
    
    try:
        # Extract from left
        left_result = _extract_and_parse_single_image(left_path, model, model_name, path.name)
        # Extract from right
        right_result = _extract_and_parse_single_image(right_path, model, model_name, path.name)
        
        # Merge questions
        merged_questions = left_result.questions + right_result.questions
        merged_result = ExtractionResult(source_file=path.name, questions=merged_questions)
        return merged_result.model_dump_json(indent=2)
    finally:
        # Clean up temp files
        if left_path.is_file():
            left_path.unlink()
        if right_path.is_file():
            right_path.unlink()



def invoke_json_repair(raw_response: str, model_name: str) -> str:
    """Use one bounded repair attempt for non-JSON model responses."""
    model = ChatOllama(model=model_name, temperature=0, num_predict=4096, num_ctx=8192)
    response = model.invoke(REPAIR_PROMPT + raw_response)
    return _as_text(response.content)


def parse_extraction(raw_response: str, source_file: str) -> ExtractionResult:
    """Parse direct JSON or JSON wrapped in a Markdown code fence."""
    candidate = _json_candidate(raw_response)
    payload = json.loads(candidate)
    # Source provenance comes from the CLI input, never from model-generated text.
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
