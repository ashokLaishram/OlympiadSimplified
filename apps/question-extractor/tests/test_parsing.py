import pytest

from sof_extractor.extractor import parse_extraction, validate_image


def test_parse_extraction_uses_input_source_filename() -> None:
    result = parse_extraction(
        '{"source_file": "made-up.png", "questions": [{"number": "1", "text": "What?"}]}',
        "page.png",
    )

    assert result.source_file == "page.png"
    assert result.questions[0].text == "What?"


def test_parse_extraction_accepts_json_fence() -> None:
    result = parse_extraction('```json\n{"source_file": "a.png", "questions": []}\n```', "page.png")

    assert result.source_file == "page.png"


def test_validate_image_rejects_other_extensions(tmp_path) -> None:
    text_file = tmp_path / "not-image.txt"
    text_file.write_text("not a PNG")

    with pytest.raises(ValueError, match="Only PNG and JPEG"):
        validate_image(str(text_file))
