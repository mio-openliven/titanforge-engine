from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan
from titanforge.exporters.minecraft_12111_request import (
    MinecraftExportRequest,
    build_minecraft_export_request,
)
from titanforge.versions.material_profile import PRIMARY_MATERIAL_TARGET


CHUNK_PLAN_SCHEMA = "titanforge.minecraft-chunk-plan"
CHUNK_PLAN_VERSION = 1
CHUNK_SIZE = 16


@dataclass(frozen=True)
class ChunkCoverage:
    source_type: str
    source_id: str
    operation: str
    chunk_x: int
    chunk_z: int
    chunk_width: int
    chunk_length: int


@dataclass(frozen=True)
class MinecraftChunkPlan:
    target_version: str
    supported: bool
    export_mode: str
    chunk_size: int
    notes: tuple[str, ...]
    coverages: tuple[ChunkCoverage, ...]


def build_minecraft_chunk_plan(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
) -> MinecraftChunkPlan:
    request = build_minecraft_export_request(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    return build_minecraft_chunk_plan_from_request(request)


def build_minecraft_chunk_plan_from_request(request: MinecraftExportRequest) -> MinecraftChunkPlan:
    if not request.supported:
        return MinecraftChunkPlan(
            target_version=request.target_version,
            supported=False,
            export_mode="unsupported",
            chunk_size=CHUNK_SIZE,
            notes=request.notes + (
                f"No chunk plan adapter is implemented yet for Minecraft {request.target_version}.",
            ),
            coverages=(),
        )

    coverages: list[ChunkCoverage] = []

    for band in request.region_bands:
        coverages.append(
            _rect_coverage(
            source_type="region-band",
            source_id=band.id,
            operation=band.operation,
            x=band.x,
            z=band.z,
            width=band.width,
            length=band.length,
        )
        )

    for band in request.transition_bands:
        coverages.append(
            _rect_coverage(
            source_type="transition-band",
            source_id=band.id,
            operation=band.operation,
            x=band.x,
            z=band.z,
            width=band.width,
            length=band.length,
        )
        )

    for road in request.road_strips:
        radius = max(1, road.width_blocks // 2)
        min_x = min(road.from_x, road.to_x) - radius
        max_x = max(road.from_x, road.to_x) + radius
        min_z = min(road.from_z, road.to_z) - radius
        max_z = max(road.from_z, road.to_z) + radius
        coverages.append(
            _rect_coverage(
            source_type="road-strip",
            source_id=road.id,
            operation=road.operation,
            x=min_x,
            z=min_z,
            width=max_x - min_x + 1,
            length=max_z - min_z + 1,
        )
        )

    for pad in request.settlement_pads:
        coverages.append(
            _rect_coverage(
            source_type="settlement-pad",
            source_id=pad.id,
            operation=pad.operation,
            x=pad.x,
            z=pad.z,
            width=pad.width,
            length=pad.length,
        )
        )

    return MinecraftChunkPlan(
        target_version=request.target_version,
        supported=True,
        export_mode=request.export_mode,
        chunk_size=CHUNK_SIZE,
        notes=request.notes + (
            f"This chunk plan is aligned to Minecraft {PRIMARY_MATERIAL_TARGET} chunk coordinates.",
        ),
        coverages=tuple(coverages),
    )


def write_minecraft_chunk_plan(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plan = build_minecraft_chunk_plan(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_text(json.dumps(minecraft_chunk_plan_to_dict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def minecraft_chunk_plan_to_dict(plan: MinecraftChunkPlan) -> dict[str, Any]:
    return {
        "schema": CHUNK_PLAN_SCHEMA,
        "version": CHUNK_PLAN_VERSION,
        "adapter": {
            "targetVersion": plan.target_version,
            "supported": plan.supported,
            "exportMode": plan.export_mode,
            "chunkSize": plan.chunk_size,
        },
        "notes": list(plan.notes),
        "coverages": [
            {
                "sourceType": coverage.source_type,
                "sourceId": coverage.source_id,
                "operation": coverage.operation,
                "chunkBounds": {
                    "x": coverage.chunk_x,
                    "z": coverage.chunk_z,
                    "width": coverage.chunk_width,
                    "length": coverage.chunk_length,
                },
            }
            for coverage in plan.coverages
        ],
    }


def _rect_coverage(
    *,
    source_type: str,
    source_id: str,
    operation: str,
    x: int,
    z: int,
    width: int,
    length: int,
) -> ChunkCoverage:
    start_x = max(0, x)
    start_z = max(0, z)
    end_x = max(start_x, x + width - 1)
    end_z = max(start_z, z + length - 1)
    chunk_x = start_x // CHUNK_SIZE
    chunk_z = start_z // CHUNK_SIZE
    chunk_width = (end_x // CHUNK_SIZE) - chunk_x + 1
    chunk_length = (end_z // CHUNK_SIZE) - chunk_z + 1
    return ChunkCoverage(
        source_type=source_type,
        source_id=source_id,
        operation=operation,
        chunk_x=chunk_x,
        chunk_z=chunk_z,
        chunk_width=chunk_width,
        chunk_length=chunk_length,
    )
