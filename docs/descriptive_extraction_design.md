# Design Doc: Multi-Modal Descriptive Question Extraction for Roblox Scene Generation

## 1. Overview & Core Philosophy

The current `sof-question-extractor` acts primarily as an OCR tool, transcribing text from Olympiad exam pages. However, this approach leaves major gaps:
1. **Empty Visual Options:** Multiple-choice options that are purely graphical (e.g., abacuses, geometric shapes) cannot be transcribed as text and appear blank.
2. **Missing Context for 3D Recreation:** In competitive exams like the SOF IMO, questions are heavily visual (e.g., counting objects, comparing weights, reading number lines). Simple text transcription lacks the descriptions needed to recreate the scenario in 3D.

To bridge this gap, this document proposes shifting to **Multi-Modal Descriptive Extraction**. Instead of transcribing *only* printed text, the Vision Language Model (VLM) is instructed to comprehend and describe the entire context (text + graphics) in a unified, structured schema ready for conversion into interactive 3D scenes (e.g., in Roblox).

---

## 2. Roblox Integration Use Case

By extracting structured scene descriptions, we can automate the creation of 3D minigames where users "play" the question:
* **Counting Questions:** Instead of reading *"How many butterflies are there?"*, a Roblox script parses the JSON, spawns the exact number of butterfly assets in a 3D garden, and lets the player count them.
* **Abacus/Number Line Questions:** Interactive abacus stands or 3D stepping-stones representing number lines are generated dynamically based on the visual attributes extracted by the model.

---

## 3. Proposed Schema Upgrades

To support this synthesis, the Pydantic data contracts in `schemas.py` will be expanded to capture detailed descriptions of layout, objects, and interactivity.

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class VisualObject(BaseModel):
    """An individual entity represented in the diagram or illustration."""
    name: str = Field(
        description="The entity name, e.g., 'butterfly', 'abacus bead', 'apple'."
    )
    quantity: int = Field(
        description="The exact count of this entity visible in the illustration."
    )
    color: Optional[str] = Field(
        default=None,
        description="The color of the entity if distinct or relevant."
    )
    spatial_layout: Optional[str] = Field(
        default=None,
        description="Spatial description (e.g., 'on the left branch of the tree', 'inside the brown basket')."
    )

class RobloxSceneMetadata(BaseModel):
    """Metadata indicating how this question should be generated as a 3D scene."""
    environment_theme: str = Field(
        description="Suggested environment style, e.g., 'Garden', 'Classroom', 'Forest', 'Market'."
    )
    interactive_elements: List[str] = Field(
        default_factory=list,
        description="List of assets the player can interact with (e.g., ['Abacus rods', 'Apples to count'])."
    )
    visual_objects: List[VisualObject] = Field(
        default_factory=list,
        description="List of all unique objects that should be spawned in the scene."
    )

class Option(BaseModel):
    """A multiple-choice option. Can be textual or descriptive."""
    label: str = Field(description="Option label, e.g., A, B, C, or D.")
    text: str = Field(
        description="Transcribed option text. If the option is a diagram/figure, provide a detailed description of the graphic instead."
    )

class Question(BaseModel):
    """The full question data contract containing textual, visual, and Roblox metadata."""
    number: str = Field(description="Printed question number.")
    text: str = Field(description="Question text, excluding the answer options.")
    options: List[Option] = Field(default_factory=list)
    visual_description: Optional[str] = Field(
        default=None,
        description="Detailed transcription of all visual elements, diagrams, tables, or graphs."
    )
    unified_description: str = Field(
        description="A cohesive, natural language summary merging the query and visuals into a clear scenario description."
    )
    roblox_scene: Optional[RobloxSceneMetadata] = Field(
        default=None,
        description="Structured scene configuration parameters for Roblox generation."
    )
```

---

## 4. Prompt Modifications

The system prompt for the VLM (`EXTRACTION_PROMPT`) must be updated to enforce visual comprehension:

```text
You are transcribing and synthesizing a SOF Olympiad question page.
Your job is to read every visible question, including its options and illustrations, and generate a structured description of the entire question scene.

For each question:
1. Extract the printed question text as-is.
2. In 'visual_description', provide an objective, detailed breakdown of any diagram, illustration, or table. Count all objects accurately (e.g., count the beads on the abacus, count butterflies, note coordinates on a number line).
3. In 'unified_description', synthesize both the question text and the illustration into a single, cohesive scenario description that can be fed into a game engine.
4. If options A, B, C, or D are images or diagrams, write a clear visual description of the diagram in the option's 'text' field rather than leaving it empty.
5. In 'roblox_scene', provide structured parameters detailing the theme, interactive targets, and object lists for automatic 3D generation.
```

---

## 5. Implementation Roadmap

To deploy this architecture, the following steps should be executed:
1. **Update Schemas & Prompts:** Integrate the Pydantic schemas and system prompt changes detailed above.
2. **Incorporate Image Splitting (Resolution Enhancement):** Introduce a pre-processing node in the LangGraph that splits double-page spreads into single columns/pages. This prevents downscaling distortion, enabling the VLM to read fine visual details (like abacus beads).
3. **Refine Markdown Renderer:** Update `markdown.py` to neatly display `visual_description`, `unified_description`, and the structured Roblox metadata.
