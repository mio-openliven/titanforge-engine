from __future__ import annotations

from pathlib import Path

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan
from titanforge.exporters.minecraft_12111_block_fixture import build_minecraft_block_fixture
from titanforge.exporters.nbt_codec import write_nbt


def write_minecraft_nbt_fixture(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = build_minecraft_block_fixture(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    payload = {
        "targetVersion": fixture.target_version,
        "supported": fixture.supported,
        "baseY": fixture.base_y,
        "notes": list(fixture.notes),
        "cuboids": [
            {
                "id": cuboid.id,
                "sourceType": cuboid.source_type,
                "operation": cuboid.operation,
                "x": cuboid.x,
                "y": cuboid.y,
                "z": cuboid.z,
                "width": cuboid.width,
                "height": cuboid.height,
                "length": cuboid.length,
                "primaryBlock": cuboid.primary_block,
                "accentBlocks": list(cuboid.accent_blocks),
            }
            for cuboid in fixture.cuboids
        ],
    }
    output_path.write_bytes(write_nbt("TitanForgeFixture", payload))
    return output_path
