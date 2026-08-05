from sof_extractor.markdown import render_markdown
from sof_extractor.schemas import ExtractionResult, Option, Question


def test_render_markdown_renders_options_and_uncertainty() -> None:
    extraction = ExtractionResult(
        source_file="page.png",
        questions=[
            Question(
                number="1",
                text="Which number is greater?",
                options=[Option(label="A", text="12"), Option(label="B", text="21")],
                uncertain_text=["Last digit near option B"],
            )
        ],
    )

    markdown = render_markdown(extraction)

    assert "## Question 1" in markdown
    assert "- A. 12" in markdown
    assert "> - Last digit near option B" in markdown
