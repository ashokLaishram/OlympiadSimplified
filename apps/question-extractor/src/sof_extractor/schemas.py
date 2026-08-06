"""Validated, model-independent data contracts for extracted questions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VisualObject(BaseModel):
    """An individual entity represented in the diagram or illustration."""

    name: str = Field(description="The entity name, e.g., 'butterfly', 'abacus bead', 'apple'.")
    quantity: int = Field(description="The exact count of this entity visible in the illustration.")
    color: str | None = Field(default=None, description="The color of the entity if distinct or relevant.")
    spatial_layout: str | None = Field(
        default=None,
        description="Spatial description (e.g., 'on the left branch of the tree', 'inside the brown basket').",
    )


class RobloxSceneMetadata(BaseModel):
    """Metadata indicating how this question should be generated as a 3D scene."""

    environment_theme: str = Field(description="Suggested environment style, e.g., 'Garden', 'Classroom', 'Forest', 'Market'.")
    interactive_elements: list[str] = Field(
        default_factory=list,
        description="List of assets the player can interact with (e.g., ['Abacus rods', 'Apples to count'])."
    )
    visual_objects: list[VisualObject] = Field(
        default_factory=list,
        description="List of all unique objects that should be spawned in the scene."
    )


class Option(BaseModel):
    """One multiple-choice answer option."""

    label: str = Field(description="Option label, typically A, B, C, or D.")
    text: str = Field(
        description="Transcribed option text. If the option is a diagram/figure, provide a detailed description of the graphic instead."
    )


class Question(BaseModel):
    """A question extracted from one source image."""

    number: str = Field(description="Printed question number.")
    text: str = Field(description="Question text, excluding the answer options.")
    options: list[Option] = Field(default_factory=list)
    image_description: str | None = Field(
        default=None,
        description="Short placeholder description for a required figure, table, or diagram.",
    )
    visual_description: str | None = Field(
        default=None,
        description="Detailed transcription of all visual elements, diagrams, tables, or graphs associated with the question."
    )
    unified_description: str = Field(
        default="",
        description="A cohesive, natural language summary merging the query and visuals into a clear scenario description."
    )
    roblox_scene: RobloxSceneMetadata | None = Field(
        default=None,
        description="Structured scene configuration parameters for Roblox generation."
    )
    uncertain_text: list[str] = Field(
        default_factory=list,
        description="Exact snippets that could not be read confidently.",
    )


class ExtractionResult(BaseModel):
    """The canonical output that later graphs should consume."""

    source_file: str
    questions: list[Question] = Field(default_factory=list)

