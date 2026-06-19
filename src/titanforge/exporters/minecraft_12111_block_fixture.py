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


BLOCK_FIXTURE_SCHEMA = "titanforge.minecraft-block-fixture"
BLOCK_FIXTURE_VERSION = 1
FIXTURE_BASE_Y = 64


@dataclass(frozen=True)
class BlockFixtureCuboid:
    id: str
    source_type: str
    operation: str
    x: int
    y: int
    z: int
    width: int
    height: int
    length: int
    primary_block: str
    accent_blocks: tuple[str, ...]


@dataclass(frozen=True)
class MinecraftBlockFixture:
    target_version: str
    supported: bool
    base_y: int
    notes: tuple[str, ...]
    cuboids: tuple[BlockFixtureCuboid, ...]


def build_minecraft_block_fixture(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
) -> MinecraftBlockFixture:
    request = build_minecraft_export_request(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    return build_minecraft_block_fixture_from_request(request)


def build_minecraft_block_fixture_from_request(request: MinecraftExportRequest) -> MinecraftBlockFixture:
    if not request.supported:
        return MinecraftBlockFixture(
            target_version=request.target_version,
            supported=False,
            base_y=FIXTURE_BASE_Y,
            notes=request.notes + (
                f"No block fixture adapter is implemented yet for Minecraft {request.target_version}.",
            ),
            cuboids=(),
        )

    cuboids: list[BlockFixtureCuboid] = []

    for band in request.region_bands:
        cuboids.append(
            BlockFixtureCuboid(
                id=band.id,
                source_type="region-band",
                operation=band.operation,
                x=band.x,
                y=FIXTURE_BASE_Y,
                z=band.z,
                width=band.width,
                height=3,
                length=band.length,
                primary_block=band.fill.primary_block,
                accent_blocks=band.fill.accent_blocks,
            )
        )

    for band in request.transition_bands:
        cuboids.append(
            BlockFixtureCuboid(
                id=band.id,
                source_type="transition-band",
                operation=band.operation,
                x=band.x,
                y=FIXTURE_BASE_Y + 3,
                z=band.z,
                width=band.width,
                height=1,
                length=band.length,
                primary_block=band.fill.primary_block,
                accent_blocks=band.fill.accent_blocks,
            )
        )

    for road in request.road_strips:
        radius = max(1, road.width_blocks // 2)
        min_x = min(road.from_x, road.to_x) - radius
        max_x = max(road.from_x, road.to_x) + radius
        min_z = min(road.from_z, road.to_z) - radius
        max_z = max(road.from_z, road.to_z) + radius
        cuboids.append(
            BlockFixtureCuboid(
                id=road.id,
                source_type="road-strip",
                operation=road.operation,
                x=min_x,
                y=FIXTURE_BASE_Y + 4,
                z=min_z,
                width=max_x - min_x + 1,
                height=1,
                length=max_z - min_z + 1,
                primary_block=road.fill.primary_block,
                accent_blocks=road.fill.accent_blocks,
            )
        )

    for pad in request.settlement_pads:
        cuboids.append(
            BlockFixtureCuboid(
                id=pad.id,
                source_type="settlement-pad",
                operation=pad.operation,
                x=pad.x,
                y=FIXTURE_BASE_Y + 5,
                z=pad.z,
                width=pad.width,
                height=2,
                length=pad.length,
                primary_block=pad.fill.primary_block,
                accent_blocks=pad.fill.accent_blocks,
            )
        )

    return MinecraftBlockFixture(
        target_version=request.target_version,
        supported=True,
        base_y=FIXTURE_BASE_Y,
        notes=request.notes + (
            f"This block fixture is aligned to the primary exporter target {PRIMARY_MATERIAL_TARGET}.",
            "It emits simple cuboids for fixture and NBT-oriented experiments, not final terrain-aware output.",
        ),
        cuboids=tuple(cuboids),
    )


def write_minecraft_block_fixture(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = build_minecraft_block_fixture(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_text(json.dumps(minecraft_block_fixture_to_dict(fixture), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def minecraft_block_fixture_to_dict(fixture: MinecraftBlockFixture) -> dict[str, Any]:
    return {
        "schema": BLOCK_FIXTURE_SCHEMA,
        "version": BLOCK_FIXTURE_VERSION,
        "adapter": {
            "targetVersion": fixture.target_version,
            "supported": fixture.supported,
            "baseY": fixture.base_y,
        },
        "notes": list(fixture.notes),
        "cuboids": [
            {
                "id": cuboid.id,
                "sourceType": cuboid.source_type,
                "operation": cuboid.operation,
                "origin": {"x": cuboid.x, "y": cuboid.y, "z": cuboid.z},
                "size": {"width": cuboid.width, "height": cuboid.height, "length": cuboid.length},
                "fill": {
                    "primaryBlock": cuboid.primary_block,
                    "accentBlocks": list(cuboid.accent_blocks),
                },
            }
            for cuboid in fixture.cuboids
        ],
    }
