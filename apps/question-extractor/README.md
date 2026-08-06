# SOF Question Extractor

Extract SOF-style multiple-choice questions from a PNG or JPEG using a local Ollama vision model, then save both validated JSON and Markdown.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) running locally
- A vision-capable model. This project defaults to the installed `gemma4:latest`.

## Install

```bash
cd sof-question-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Extract a PNG

```bash
python -m sof_extractor input/page_01.jpeg --output output/page_01.md
```

The command also creates `output/page_01.json`. To choose another installed Ollama model:

```bash
python -m sof_extractor input/page_01.png --model gemma4:latest
```

Only single PNG or JPEG files are supported in v1. The model is instructed to transcribe, not solve. Any unclear text is kept in `uncertain_text` rather than guessed.
