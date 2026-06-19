from __future__ import annotations

from pathlib import Path

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan
from titanforge.exporters.minecraft_12111_block_fixture import MinecraftBlockFixture, build_minecraft_block_fixture


MAX_FILL_STRIPE = 32


def write_minecraft_mcfunction_fixture(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = build_minecraft_block_fixture(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_text("\n".join(build_mcfunction_lines(fixture)) + "\n", encoding="utf-8")
    return output_path


def write_minecraft_clear_mcfunction_fixture(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = build_minecraft_block_fixture(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_text("\n".join(build_clear_mcfunction_lines(fixture)) + "\n", encoding="utf-8")
    return output_path


def build_mcfunction_lines(fixture: MinecraftBlockFixture) -> tuple[str, ...]:
    lines: list[str] = [
        "# TitanForge 1.21.11 fixture mcfunction",
        f"# target version: {fixture.target_version}",
    ]
    lines.extend(f"# note: {note}" for note in fixture.notes)

    if not fixture.supported:
        lines.append("# unsupported target; no fill commands emitted")
        return tuple(lines)

    for cuboid in fixture.cuboids:
        lines.append(
            f"# {cuboid.source_type} {cuboid.id} primary={cuboid.primary_block} "
            f"accents={','.join(cuboid.accent_blocks)}"
        )
        lines.extend(_cuboid_fill_commands(cuboid))

    return tuple(lines)


def build_clear_mcfunction_lines(fixture: MinecraftBlockFixture) -> tuple[str, ...]:
    lines: list[str] = [
        "# TitanForge 1.21.11 clear fixture mcfunction",
        f"# target version: {fixture.target_version}",
    ]
    lines.extend(f"# note: {note}" for note in fixture.notes)

    if not fixture.supported:
        lines.append("# unsupported target; no clear commands emitted")
        return tuple(lines)

    for cuboid in fixture.cuboids:
        lines.append(f"# clear {cuboid.source_type} {cuboid.id}")
        lines.extend(_cuboid_fill_commands(cuboid, block_name="air"))

    return tuple(lines)


def count_mcfunction_fill_commands(fixture: MinecraftBlockFixture) -> int:
    if not fixture.supported:
        return 0
    return sum(len(_cuboid_fill_commands(cuboid)) for cuboid in fixture.cuboids)


def _cuboid_fill_commands(cuboid, *, block_name: str | None = None) -> tuple[str, ...]:
    commands: list[str] = []
    if cuboid.width >= cuboid.length:
        stripe_axis = "x"
        stripe_total = cuboid.width
    else:
        stripe_axis = "z"
        stripe_total = cuboid.length

    offset = 0
    while offset < stripe_total:
        stripe_size = min(MAX_FILL_STRIPE, stripe_total - offset)
        start_x = cuboid.x + offset if stripe_axis == "x" else cuboid.x
        end_x = start_x + stripe_size - 1 if stripe_axis == "x" else cuboid.x + cuboid.width - 1
        start_z = cuboid.z + offset if stripe_axis == "z" else cuboid.z
        end_z = start_z + stripe_size - 1 if stripe_axis == "z" else cuboid.z + cuboid.length - 1
        end_y = cuboid.y + cuboid.height - 1
        commands.append(
            f"fill {start_x} {cuboid.y} {start_z} {end_x} {end_y} {end_z} {block_name or cuboid.primary_block}"
        )
        offset += stripe_size

    return tuple(commands)
