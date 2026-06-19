from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan
from titanforge.versions.material_profile import MaterialAssignment, MaterialProfile, PRIMARY_MATERIAL_TARGET, build_material_profile


EXPORT_REQUEST_SCHEMA = "titanforge.minecraft-export-request"
EXPORT_REQUEST_VERSION = 1


@dataclass(frozen=True)
class ExportFill:
    palette_id: str
    primary_block: str
    accent_blocks: tuple[str, ...]


@dataclass(frozen=True)
class ExportRegionBand:
    id: str
    kind: str
    x: int
    z: int
    width: int
    length: int
    fill: ExportFill
    operation: str


@dataclass(frozen=True)
class ExportTransitionBand:
    id: str
    kind: str
    x: int
    z: int
    width: int
    length: int
    fill: ExportFill
    operation: str


@dataclass(frozen=True)
class ExportRoadStrip:
    id: str
    kind: str
    width_blocks: int
    from_x: int
    from_z: int
    to_x: int
    to_z: int
    fill: ExportFill
    operation: str


@dataclass(frozen=True)
class ExportSettlementPad:
    id: str
    kind: str
    x: int
    z: int
    width: int
    length: int
    access_roads: tuple[str, ...]
    fill: ExportFill
    operation: str


@dataclass(frozen=True)
class MinecraftExportRequest:
    target_version: str
    supported: bool
    export_mode: str
    notes: tuple[str, ...]
    region_bands: tuple[ExportRegionBand, ...]
    transition_bands: tuple[ExportTransitionBand, ...]
    road_strips: tuple[ExportRoadStrip, ...]
    settlement_pads: tuple[ExportSettlementPad, ...]


def build_minecraft_export_request(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
) -> MinecraftExportRequest:
    material_profile = build_material_profile(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    return build_minecraft_export_request_from_profile(
        material_profile,
        world_plan,
        transition_plan,
        road_plan,
        settlement_plan,
    )


def build_minecraft_export_request_from_profile(
    material_profile: MaterialProfile,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
) -> MinecraftExportRequest:
    if not material_profile.supported:
        return MinecraftExportRequest(
            target_version=material_profile.target_version,
            supported=False,
            export_mode="unsupported",
            notes=material_profile.notes + (
                f"No export request adapter is implemented yet for Minecraft {material_profile.target_version}.",
            ),
            region_bands=(),
            transition_bands=(),
            road_strips=(),
            settlement_pads=(),
        )

    region_materials = {assignment.id: assignment for assignment in material_profile.region_materials}
    transition_materials = {assignment.id: assignment for assignment in material_profile.transition_materials}
    road_materials = {assignment.id: assignment for assignment in material_profile.road_materials}
    settlement_materials = {assignment.id: assignment for assignment in material_profile.settlement_materials}

    return MinecraftExportRequest(
        target_version=material_profile.target_version,
        supported=True,
        export_mode="schematic-fixture",
        notes=material_profile.notes + (
            f"This request is shaped for the primary exporter target {PRIMARY_MATERIAL_TARGET}.",
            "It describes fill bands and pads, not final chunk or NBT output.",
        ),
        region_bands=tuple(
            ExportRegionBand(
                id=region.title,
                kind=region.kind,
                x=region.x,
                z=region.z,
                width=region.width,
                length=region.length,
                fill=_fill_from_assignment(region_materials[region.title]),
                operation="surface-zone",
            )
            for region in world_plan.regions
        ),
        transition_bands=tuple(
            ExportTransitionBand(
                id=transition.id,
                kind=transition.kind,
                x=transition.x,
                z=transition.z,
                width=transition.width,
                length=transition.length,
                fill=_fill_from_assignment(transition_materials[transition.id]),
                operation="blend-band",
            )
            for transition in transition_plan.transitions
        ),
        road_strips=tuple(
            ExportRoadStrip(
                id=road.id,
                kind=road.kind,
                width_blocks=_road_width_blocks(road.width_hint),
                from_x=road.from_point.x,
                from_z=road.from_point.z,
                to_x=road.to_point.x,
                to_z=road.to_point.z,
                fill=_fill_from_assignment(road_materials[road.id]),
                operation="path-strip",
            )
            for road in road_plan.roads
        ),
        settlement_pads=tuple(
            ExportSettlementPad(
                id=blockout.id,
                kind=blockout.kind,
                x=blockout.x,
                z=blockout.z,
                width=blockout.width,
                length=blockout.length,
                access_roads=blockout.access_roads,
                fill=_fill_from_assignment(settlement_materials[blockout.id]),
                operation="foundation-pad",
            )
            for blockout in settlement_plan.blockouts
        ),
    )


def write_minecraft_export_request(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    request = build_minecraft_export_request(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    output_path.write_text(json.dumps(minecraft_export_request_to_dict(request), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def minecraft_export_request_to_dict(request: MinecraftExportRequest) -> dict[str, Any]:
    return {
        "schema": EXPORT_REQUEST_SCHEMA,
        "version": EXPORT_REQUEST_VERSION,
        "adapter": {
            "targetVersion": request.target_version,
            "supported": request.supported,
            "exportMode": request.export_mode,
            "primaryTarget": PRIMARY_MATERIAL_TARGET,
        },
        "notes": list(request.notes),
        "regionBands": [
            {
                "id": band.id,
                "kind": band.kind,
                "bounds": {"x": band.x, "z": band.z, "width": band.width, "length": band.length},
                "operation": band.operation,
                "fill": _fill_to_dict(band.fill),
            }
            for band in request.region_bands
        ],
        "transitionBands": [
            {
                "id": band.id,
                "kind": band.kind,
                "bounds": {"x": band.x, "z": band.z, "width": band.width, "length": band.length},
                "operation": band.operation,
                "fill": _fill_to_dict(band.fill),
            }
            for band in request.transition_bands
        ],
        "roadStrips": [
            {
                "id": road.id,
                "kind": road.kind,
                "widthBlocks": road.width_blocks,
                "from": {"x": road.from_x, "z": road.from_z},
                "to": {"x": road.to_x, "z": road.to_z},
                "operation": road.operation,
                "fill": _fill_to_dict(road.fill),
            }
            for road in request.road_strips
        ],
        "settlementPads": [
            {
                "id": pad.id,
                "kind": pad.kind,
                "origin": {"x": pad.x, "z": pad.z},
                "size": {"width": pad.width, "length": pad.length},
                "accessRoads": list(pad.access_roads),
                "operation": pad.operation,
                "fill": _fill_to_dict(pad.fill),
            }
            for pad in request.settlement_pads
        ],
    }


def _fill_from_assignment(assignment: MaterialAssignment) -> ExportFill:
    return ExportFill(
        palette_id=assignment.palette_id,
        primary_block=assignment.primary_block,
        accent_blocks=assignment.accent_blocks,
    )


def _fill_to_dict(fill: ExportFill) -> dict[str, Any]:
    return {
        "paletteId": fill.palette_id,
        "primaryBlock": fill.primary_block,
        "accentBlocks": list(fill.accent_blocks),
    }


def _road_width_blocks(width_hint: str) -> int:
    if width_hint == "wide":
        return 5
    return 3
