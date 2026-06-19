from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan
from titanforge.exporters.minecraft_12111_block_fixture import MinecraftBlockFixture, build_minecraft_block_fixture
from titanforge.exporters.minecraft_12111_datapack import CLEAR_FUNCTION_ID, PLACE_FUNCTION_ID
from titanforge.exporters.minecraft_12111_mcfunction import count_mcfunction_fill_commands


FIXTURE_SUMMARY_SCHEMA = "titanforge.minecraft-fixture-summary"
FIXTURE_SUMMARY_VERSION = 1
MAX_SAFE_FILL_COMMANDS = 256
MAX_SAFE_FOOTPRINT_SIDE = 1024
MAX_SAFE_CUBOIDS = 64


def write_minecraft_fixture_summary(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = build_minecraft_block_fixture(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_text(json.dumps(build_minecraft_fixture_summary_dict(fixture), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def build_minecraft_fixture_summary_dict(fixture: MinecraftBlockFixture) -> dict[str, Any]:
    fill_command_count = count_mcfunction_fill_commands(fixture)
    bounds = _build_bounds(fixture)
    warnings = _build_warnings(fixture, bounds, fill_command_count)
    return {
        "schema": FIXTURE_SUMMARY_SCHEMA,
        "version": FIXTURE_SUMMARY_VERSION,
        "adapter": {
            "targetVersion": fixture.target_version,
            "supported": fixture.supported,
            "baseY": fixture.base_y,
        },
        "functionIds": {
            "place": PLACE_FUNCTION_ID,
            "clear": CLEAR_FUNCTION_ID,
        },
        "counts": {
            "cuboids": len(fixture.cuboids),
            "placeFillCommands": fill_command_count,
            "clearFillCommands": fill_command_count,
        },
        "bounds": bounds,
        "warnings": warnings,
        "notes": list(fixture.notes),
    }


def _build_bounds(fixture: MinecraftBlockFixture) -> dict[str, int] | None:
    if not fixture.cuboids:
        return None

    min_x = min(cuboid.x for cuboid in fixture.cuboids)
    min_y = min(cuboid.y for cuboid in fixture.cuboids)
    min_z = min(cuboid.z for cuboid in fixture.cuboids)
    max_x = max(cuboid.x + cuboid.width - 1 for cuboid in fixture.cuboids)
    max_y = max(cuboid.y + cuboid.height - 1 for cuboid in fixture.cuboids)
    max_z = max(cuboid.z + cuboid.length - 1 for cuboid in fixture.cuboids)
    return {
        "minX": min_x,
        "minY": min_y,
        "minZ": min_z,
        "maxX": max_x,
        "maxY": max_y,
        "maxZ": max_z,
        "width": max_x - min_x + 1,
        "height": max_y - min_y + 1,
        "length": max_z - min_z + 1,
    }


def _build_warnings(
    fixture: MinecraftBlockFixture,
    bounds: dict[str, int] | None,
    fill_command_count: int,
) -> list[str]:
    warnings: list[str] = []

    if not fixture.supported:
        warnings.append(
            f"No supported 1.21.11 fixture export is available for requested target {fixture.target_version}."
        )
        return warnings

    if len(fixture.cuboids) > MAX_SAFE_CUBOIDS:
        warnings.append(
            f"Fixture complexity is high: {len(fixture.cuboids)} cuboids exceed the starter comfort limit of {MAX_SAFE_CUBOIDS}."
        )

    if fill_command_count > MAX_SAFE_FILL_COMMANDS:
        warnings.append(
            f"Fixture command load is high: {fill_command_count} fill commands exceed the starter comfort limit of {MAX_SAFE_FILL_COMMANDS}."
        )

    if bounds is not None and max(bounds["width"], bounds["length"]) > MAX_SAFE_FOOTPRINT_SIDE:
        warnings.append(
            "Fixture footprint is large: at least one side exceeds "
            f"{MAX_SAFE_FOOTPRINT_SIDE} blocks. Test in a disposable world first."
        )

    return warnings
