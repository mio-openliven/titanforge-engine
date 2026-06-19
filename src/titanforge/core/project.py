from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class ProjectRegion:
    title: str
    kind: str
    story_role: str
    mood: str
    coverage_hint: str
    notes: str


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    target_version: str
    width: int
    length: int
    premise: str
    player_experience: str
    regions: tuple[ProjectRegion, ...]
    pipeline: tuple[str, ...]


def load_project_config(path: Path) -> ProjectConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    project = data.get("project", {})
    world = data.get("world", {})
    creative = data.get("creative", {})
    regions_data = data.get("regions", [])
    pipeline = data.get("pipeline", {})

    return ProjectConfig(
        name=str(project.get("name", "Unnamed TitanForge Project")),
        target_version=str(project.get("target_version", "1.21.11")),
        width=int(world.get("width", 512)),
        length=int(world.get("length", 512)),
        premise=str(creative.get("premise", "A world brief is not written yet.")),
        player_experience=str(
            creative.get(
                "player_experience",
                "The intended player feeling is not described yet.",
            )
        ),
        regions=tuple(
            ProjectRegion(
                title=str(region.get("title", "Unnamed Region")),
                kind=str(region.get("kind", "unknown")),
                story_role=str(region.get("story_role", "not defined yet")),
                mood=str(region.get("mood", "not defined yet")),
                coverage_hint=str(region.get("coverage_hint", "not defined yet")),
                notes=str(region.get("notes", "No notes yet.")),
            )
            for region in regions_data
        ),
        pipeline=tuple(str(stage) for stage in pipeline.get("stages", [])),
    )
