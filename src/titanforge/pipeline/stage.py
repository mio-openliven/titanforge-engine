from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class StageResult:
    name: str
    artifacts: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


class Stage(Protocol):
    name: str

    def run(self) -> StageResult:
        """Run the pipeline stage."""


@dataclass
class Pipeline:
    stages: list[Stage] = field(default_factory=list)

    def run(self) -> list[StageResult]:
        return [stage.run() for stage in self.stages]
