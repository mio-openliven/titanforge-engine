from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan
from titanforge.exporters.minecraft_12111_block_fixture import MinecraftBlockFixture, build_minecraft_block_fixture
from titanforge.exporters.nbt_codec import read_nbt, write_nbt
from titanforge.versions.material_profile import PRIMARY_MATERIAL_TARGET


STRUCTURE_TEMPLATE_DATA_VERSION = 4671
STRUCTURE_TEMPLATE_ROOT_NAME = ""
STRUCTURE_TEMPLATE_NAME = "fixture"
STRUCTURE_TEMPLATE_ID = f"titanforge:{STRUCTURE_TEMPLATE_NAME}"
MAX_STRUCTURE_TEMPLATE_BLOCKS = 4_194_304


def write_minecraft_structure_template(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = build_minecraft_block_fixture(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_bytes(build_minecraft_structure_template_bytes(fixture))
    return output_path


def build_minecraft_structure_template_bytes(fixture: MinecraftBlockFixture) -> bytes:
    payload = build_minecraft_structure_template_payload(fixture)
    return gzip.compress(write_nbt(STRUCTURE_TEMPLATE_ROOT_NAME, payload))


def read_minecraft_structure_template(data: bytes) -> tuple[str, dict[str, Any]]:
    return read_nbt(gzip.decompress(data))


def build_minecraft_structure_template_payload(fixture: MinecraftBlockFixture) -> dict[str, Any]:
    if get_structure_template_export_issue(fixture) is not None:
        return {
            "DataVersion": STRUCTURE_TEMPLATE_DATA_VERSION,
            "size": [0, 0, 0],
            "palette": [],
            "blocks": [],
            "entities": [],
        }

    absolute_blocks = _build_absolute_block_map(fixture)
    min_x, min_y, min_z, max_x, max_y, max_z = _block_bounds(absolute_blocks)

    palette_lookup: dict[tuple[str, tuple[tuple[str, str], ...]], int] = {}
    palette: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []

    for x, y, z in sorted(absolute_blocks):
        state_key = _parse_block_state(absolute_blocks[(x, y, z)])
        if state_key not in palette_lookup:
            palette_lookup[state_key] = len(palette)
            palette.append(_state_key_to_palette_entry(state_key))
        blocks.append(
            {
                "state": palette_lookup[state_key],
                "pos": [x - min_x, y - min_y, z - min_z],
            }
        )

    return {
        "DataVersion": STRUCTURE_TEMPLATE_DATA_VERSION,
        "size": [max_x - min_x + 1, max_y - min_y + 1, max_z - min_z + 1],
        "palette": palette,
        "blocks": blocks,
        "entities": [],
    }


def estimate_minecraft_structure_template_block_count(fixture: MinecraftBlockFixture) -> int:
    return sum(cuboid.width * cuboid.height * cuboid.length for cuboid in fixture.cuboids)


def get_structure_template_export_issue(fixture: MinecraftBlockFixture) -> str | None:
    if not fixture.supported:
        return (
            f"Requested target {fixture.target_version} is not supported by the current "
            f"{PRIMARY_MATERIAL_TARGET} structure-template exporter."
        )

    estimated_block_count = estimate_minecraft_structure_template_block_count(fixture)
    if estimated_block_count > MAX_STRUCTURE_TEMPLATE_BLOCKS:
        return (
            "Fixture is too large for a safe vanilla structure-template export "
            f"({estimated_block_count:,} estimated blocks; limit {MAX_STRUCTURE_TEMPLATE_BLOCKS:,})."
        )

    return None


def _build_absolute_block_map(fixture: MinecraftBlockFixture) -> dict[tuple[int, int, int], str]:
    blocks: dict[tuple[int, int, int], str] = {}
    for cuboid in fixture.cuboids:
        for y in range(cuboid.y, cuboid.y + cuboid.height):
            for z in range(cuboid.z, cuboid.z + cuboid.length):
                for x in range(cuboid.x, cuboid.x + cuboid.width):
                    blocks[(x, y, z)] = cuboid.primary_block
    return blocks


def _block_bounds(blocks: dict[tuple[int, int, int], str]) -> tuple[int, int, int, int, int, int]:
    xs = [position[0] for position in blocks]
    ys = [position[1] for position in blocks]
    zs = [position[2] for position in blocks]
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def _parse_block_state(block_name: str) -> tuple[str, tuple[tuple[str, str], ...]]:
    raw_name, separator, raw_properties = block_name.partition("[")
    qualified_name = raw_name if ":" in raw_name else f"minecraft:{raw_name}"
    if not separator:
        return qualified_name, ()

    properties_text = raw_properties.rstrip("]")
    properties: list[tuple[str, str]] = []
    for entry in properties_text.split(","):
        key, _, value = entry.partition("=")
        if key and value:
            properties.append((key, value))
    properties.sort()
    return qualified_name, tuple(properties)


def _state_key_to_palette_entry(state_key: tuple[str, tuple[tuple[str, str], ...]]) -> dict[str, Any]:
    name, properties = state_key
    entry: dict[str, Any] = {"Name": name}
    if properties:
        entry["Properties"] = {key: value for key, value in properties}
    return entry


def build_structure_template_note_lines(fixture: MinecraftBlockFixture) -> tuple[str, ...]:
    export_issue = get_structure_template_export_issue(fixture)
    if export_issue is not None:
        return (
            export_issue,
            "Do not run /place template for this draft; use the mcfunction or datapack flow instead.",
        )
    return (
        f"Alternative vanilla structure test: /place template {STRUCTURE_TEMPLATE_ID}",
        "This uses the packaged structure-template.nbt instead of the mcfunction fill pass.",
    )
