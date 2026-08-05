"""Validated, model-independent data contracts for extracted questions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Option(BaseModel):
    """One multiple-choice answer option."""

    label: str = Field(description="Option label, typically A, B, C, or D.")
    text: str = Field(description="Option text, transcribed without solving it.")


class Question(BaseModel):
    """A question extracted from one source image."""

    number: str = Field(description="Printed question number.")
    text: str = Field(description="Question text, excluding the answer options.")
    options: list[Option] = Field(default_factory=list)
    image_description: str | None = Field(
        default=None,
        description="Short placeholder description for a required figure, table, or diagram.",
    )
    uncertain_text: list[str] = Field(
        default_factory=list,
        description="Exact snippets that could not be read confidently.",
    )


class ExtractionResult(BaseModel):
    """The canonical output that later graphs should consume."""

    source_file: str
    questions: list[Question] = Field(default_factory=list)
