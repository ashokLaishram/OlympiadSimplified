"""Command-line entry point for one-image extraction runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from .graph import build_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract SOF-style questions from one PNG with local Ollama.")
    parser.add_argument("image_path", help="Path to a PNG question page.")
    parser.add_argument("--output", "-o", help="Output Markdown path. Defaults to output/<image stem>.md.")
    parser.add_argument("--model", default="gemma4:latest", help="Local Ollama vision model to use.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_path = Path(args.image_path)
    output_path = Path(args.output) if args.output else Path("output") / f"{image_path.stem}.md"
    result = build_graph().invoke({"image_path": str(image_path), "model_name": args.model, "errors": []})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result["markdown_content"], encoding="utf-8")
    json_path = output_path.with_suffix(".json")
    json_path.write_text(result["extraction"].model_dump_json(indent=2) + "\n", encoding="utf-8")

    print(f"Markdown: {output_path}")
    print(f"JSON: {json_path}")
    for warning in result.get("errors", []):
        print(f"Warning: {warning}")


if __name__ == "__main__":
    main()
