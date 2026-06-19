from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan, WorldPlanRegion


MATERIAL_PROFILE_SCHEMA = "titanforge.minecraft-material-profile"
MATERIAL_PROFILE_VERSION = 1
PRIMARY_MATERIAL_TARGET = "1.21.11"

_ZONE_KEYWORDS = (
    ("port", ("port", "harbor", "dock")),
    ("mountain", ("mountain", "mountains", "ridge", "peak", "cliff", "highland")),
    ("forest", ("forest", "woods", "pine", "jungle", "grove")),
    ("road", ("road", "path", "bridge", "route")),
    ("city", ("city", "town", "village", "settlement", "ruins", "fort", "castle")),
    ("beach", ("beach", "dune", "sand")),
    ("water", ("sea", "ocean", "water", "bay", "coast", "shore", "lake", "river")),
    ("land", ("land", "field", "farm", "plains", "meadow", "valley")),
)

_ZONE_PALETTES = {
    "water": ("water", ("sand", "gravel", "clay")),
    "beach": ("sand", ("sandstone", "smooth_sandstone", "gravel")),
    "port": ("oak_planks", ("stone_bricks", "cobblestone", "stripped_oak_log")),
    "city": ("stone_bricks", ("cobblestone", "oak_planks", "andesite")),
    "forest": ("grass_block", ("podzol", "moss_block", "spruce_log")),
    "land": ("grass_block", ("dirt", "coarse_dirt", "oak_log")),
    "mountain": ("stone", ("andesite", "cobblestone", "gravel")),
    "road": ("gravel", ("cobblestone", "dirt_path", "andesite")),
}

_TRANSITION_PALETTES = {
    "coast-transition": ("sand", ("gravel", "water", "sandstone")),
    "treeline-rise": ("podzol", ("stone", "spruce_log", "moss_block")),
    "settled-edge": ("coarse_dirt", ("gravel", "oak_planks", "stone_bricks")),
    "soft-boundary": ("grass_block", ("coarse_dirt", "moss_block", "oak_log")),
}

_ROAD_PALETTES = {
    "main-road": ("gravel", ("cobblestone", "andesite", "stone_bricks")),
    "local-path": ("dirt_path", ("coarse_dirt", "gravel", "cobblestone")),
}

_SETTLEMENT_PALETTES = {
    "gate": ("stone_bricks", ("oak_fence", "cobblestone", "oak_planks")),
    "core": ("stone_bricks", ("oak_planks", "cobblestone", "glass_pane")),
    "harbor": ("oak_planks", ("stripped_oak_log", "cobblestone", "barrel")),
    "junction": ("gravel", ("cobblestone", "stone_bricks", "oak_fence")),
}


@dataclass(frozen=True)
class MaterialPalette:
    id: str
    primary_block: str
    accent_blocks: tuple[str, ...]


@dataclass(frozen=True)
class MaterialAssignment:
    id: str
    kind: str
    palette_id: str
    primary_block: str
    accent_blocks: tuple[str, ...]


@dataclass(frozen=True)
class MaterialProfile:
    target_version: str
    supported: bool
    notes: tuple[str, ...]
    region_materials: tuple[MaterialAssignment, ...]
    transition_materials: tuple[MaterialAssignment, ...]
    road_materials: tuple[MaterialAssignment, ...]
    settlement_materials: tuple[MaterialAssignment, ...]


def build_material_profile(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
) -> MaterialProfile:
    if target_version != PRIMARY_MATERIAL_TARGET:
        return MaterialProfile(
            target_version=target_version,
            supported=False,
            notes=(
                f"No material adapter is implemented yet for Minecraft {target_version}.",
                f"Current material adapter target: Minecraft {PRIMARY_MATERIAL_TARGET}.",
            ),
            region_materials=(),
            transition_materials=(),
            road_materials=(),
            settlement_materials=(),
        )

    region_materials = tuple(_region_assignment(region) for region in world_plan.regions)
    transition_materials = tuple(_assignment_from_palette(transition.id, transition.kind, *_TRANSITION_PALETTES[transition.kind]) for transition in transition_plan.transitions)
    road_materials = tuple(_assignment_from_palette(road.id, road.kind, *_ROAD_PALETTES[road.kind]) for road in road_plan.roads)
    settlement_materials = tuple(
        _assignment_from_palette(blockout.id, blockout.kind, *_SETTLEMENT_PALETTES[blockout.kind])
        for blockout in settlement_plan.blockouts
    )

    return MaterialProfile(
        target_version=target_version,
        supported=True,
        notes=(
            "This is the first deterministic Minecraft 1.21.11 material adapter.",
            "It maps neutral planning artifacts into starter block palettes, not final export geometry.",
        ),
        region_materials=region_materials,
        transition_materials=transition_materials,
        road_materials=road_materials,
        settlement_materials=settlement_materials,
    )


def write_material_profile(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = build_material_profile(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_text(json.dumps(material_profile_to_dict(profile), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def material_profile_to_dict(profile: MaterialProfile) -> dict[str, Any]:
    return {
        "schema": MATERIAL_PROFILE_SCHEMA,
        "version": MATERIAL_PROFILE_VERSION,
        "adapter": {
            "targetVersion": profile.target_version,
            "supported": profile.supported,
            "primaryTarget": PRIMARY_MATERIAL_TARGET,
        },
        "notes": list(profile.notes),
        "regionMaterials": [_assignment_to_dict(assignment) for assignment in profile.region_materials],
        "transitionMaterials": [_assignment_to_dict(assignment) for assignment in profile.transition_materials],
        "roadMaterials": [_assignment_to_dict(assignment) for assignment in profile.road_materials],
        "settlementMaterials": [_assignment_to_dict(assignment) for assignment in profile.settlement_materials],
    }


def _assignment_to_dict(assignment: MaterialAssignment) -> dict[str, Any]:
    return {
        "id": assignment.id,
        "kind": assignment.kind,
        "paletteId": assignment.palette_id,
        "primaryBlock": assignment.primary_block,
        "accentBlocks": list(assignment.accent_blocks),
    }


def _region_assignment(region: WorldPlanRegion) -> MaterialAssignment:
    zone_family = _zone_family(region)
    primary_block, accent_blocks = _ZONE_PALETTES[zone_family]
    return _assignment_from_palette(region.title, zone_family, primary_block, accent_blocks)


def _assignment_from_palette(
    assignment_id: str,
    kind: str,
    primary_block: str,
    accent_blocks: tuple[str, ...],
) -> MaterialAssignment:
    palette = MaterialPalette(id=kind, primary_block=primary_block, accent_blocks=accent_blocks)
    return MaterialAssignment(
        id=assignment_id,
        kind=kind,
        palette_id=palette.id,
        primary_block=palette.primary_block,
        accent_blocks=palette.accent_blocks,
    )


def _zone_family(region: WorldPlanRegion) -> str:
    text = " ".join((region.kind, region.title, region.story_role, region.notes)).lower()
    tokens = set(re.findall(r"[a-z]+", text))
    for zone_id, keywords in _ZONE_KEYWORDS:
        if any(keyword in tokens for keyword in keywords):
            return zone_id
    return "land"
