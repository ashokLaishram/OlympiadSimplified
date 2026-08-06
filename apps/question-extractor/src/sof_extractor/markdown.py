"""Deterministic rendering; the model never formats final Markdown."""

from __future__ import annotations

from .schemas import ExtractionResult


def render_markdown(extraction: ExtractionResult) -> str:
    lines = ["# Extracted SOF Questions", "", f"_Source: {extraction.source_file}_", ""]
    if not extraction.questions:
        lines.extend(["No questions were detected.", ""])
    for question in extraction.questions:
        lines.extend([f"## Question {question.number}", "", question.text, ""])
        for option in question.options:
            lines.append(f"- {option.label}. {option.text}")
        if question.options:
            lines.append("")
        if question.unified_description:
            lines.extend(["### Unified Description", "", question.unified_description, ""])
        if question.visual_description:
            lines.extend(["> **Visual Description:**", f"> {question.visual_description}", ""])
        if question.image_description:
            lines.extend(["> **Figure/table:**", f"> {question.image_description}", ""])
        
        # Render Roblox scene config
        if question.roblox_scene:
            scene = question.roblox_scene
            lines.extend(["### Roblox 3D Scene Config", "", f"* **Environment Theme:** {scene.environment_theme}"])
            if scene.interactive_elements:
                lines.append(f"* **Interactive Elements:** {', '.join(scene.interactive_elements)}")
            if scene.visual_objects:
                lines.extend(["* **Visual Objects:**", ""])
                lines.append("  | Object Name | Quantity | Color | Spatial Layout |")
                lines.append("  | :--- | :---: | :--- | :--- |")
                for obj in scene.visual_objects:
                    color_str = obj.color if obj.color else "-"
                    layout_str = obj.spatial_layout if obj.spatial_layout else "-"
                    lines.append(f"  | {obj.name} | {obj.quantity} | {color_str} | {layout_str} |")
            lines.append("")
                
        if question.uncertain_text:
            lines.extend(["> **Extraction uncertainties:**", *[f"> - {text}" for text in question.uncertain_text], ""])
    return "\n".join(lines).rstrip() + "\n"
