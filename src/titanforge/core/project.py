from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    target_version: str
    width: int
    length: int
    pipeline: tuple[str, ...]


def load_project_config(path: Path) -> ProjectConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    project = data.get("project", {})
    world = data.get("world", {})
    pipeline = data.get("pipeline", {})

    return ProjectConfig(
        name=str(project.get("name", "Unnamed TitanForge Project")),
        target_version=str(project.get("target_version", "1.21.11")),
        width=int(world.get("width", 512)),
        length=int(world.get("length", 512)),
        pipeline=tuple(str(stage) for stage in pipeline.get("stages", [])),
    )
