from __future__ import annotations

from dataclasses import dataclass
import json
from math import ceil
from pathlib import Path
import re

from titanforge.core.placement_plan import build_placement_plan, render_placement_preview, write_placement_plan
from titanforge.core.road_plan import build_road_plan, render_road_preview, write_road_plan
from titanforge.core.project import ProjectConfig
from titanforge.core.route_plan import build_route_plan, render_route_preview, write_route_plan
from titanforge.core.project_review import write_project_review_page
from titanforge.core.settlement_plan import build_settlement_plan, render_settlement_preview, write_settlement_plan
from titanforge.core.transition_plan import build_transition_plan, render_transition_preview, write_transition_plan
from titanforge.core.world_plan import WorldPlan, WorldPlanRegion, build_world_plan, write_world_plan
from titanforge.exporters.minecraft_12111_block_fixture import write_minecraft_block_fixture
from titanforge.exporters.minecraft_12111_chunk_plan import write_minecraft_chunk_plan
from titanforge.exporters.minecraft_12111_nbt_fixture import write_minecraft_nbt_fixture
from titanforge.exporters.minecraft_12111_request import write_minecraft_export_request
from titanforge.masks.palette import DEFAULT_ZONE_PALETTE
from titanforge.masks.png import write_rgba_png
from titanforge.versions.material_profile import write_material_profile


PROJECT_DRAFT_SCHEMA = "titanforge.project-draft"
PROJECT_DRAFT_VERSION = 1
DEFAULT_MAX_DRAFT_SIDE = 1024
MIN_DRAFT_SIDE = 64
MAX_DRAFT_SIDE = 4096

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


@dataclass(frozen=True)
class DraftRegion:
    title: str
    zone_id: str
    shape: str
    color: str
    x: int
    z: int
    width: int
    length: int
    raster_x: int
    raster_z: int
    raster_width: int
    raster_length: int


@dataclass(frozen=True)
class ProjectDraftResult:
    output_dir: Path
    review_page_path: Path
    world_plan_path: Path
    material_profile_path: Path
    export_request_path: Path
    chunk_plan_path: Path
    block_fixture_path: Path
    nbt_fixture_path: Path
    transition_plan_path: Path
    transition_preview_path: Path
    route_plan_path: Path
    route_preview_path: Path
    placement_plan_path: Path
    placement_preview_path: Path
    road_plan_path: Path
    road_preview_path: Path
    settlement_plan_path: Path
    settlement_preview_path: Path
    draft_mask_path: Path
    manifest_path: Path
    world_width: int
    world_length: int
    raster_width: int
    raster_length: int
    blocks_per_pixel: int
    warnings: tuple[str, ...]


def write_project_draft(config: ProjectConfig, output_dir: Path, *, max_draft_side: int = DEFAULT_MAX_DRAFT_SIDE) -> ProjectDraftResult:
    if not MIN_DRAFT_SIDE <= max_draft_side <= MAX_DRAFT_SIDE:
        raise ValueError(
            f"max_draft_side must be between {MIN_DRAFT_SIDE} and {MAX_DRAFT_SIDE}, got {max_draft_side}."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    review_page_path = output_dir / "review.html"
    world_plan_path = output_dir / "world-plan.json"
    material_profile_path = output_dir / "material-profile.json"
    export_request_path = output_dir / "export-request.json"
    chunk_plan_path = output_dir / "chunk-plan.json"
    block_fixture_path = output_dir / "block-fixture.json"
    nbt_fixture_path = output_dir / "block-fixture.nbt"
    transition_plan_path = output_dir / "transition-plan.json"
    transition_preview_path = output_dir / "transition-preview.png"
    route_plan_path = output_dir / "route-plan.json"
    route_preview_path = output_dir / "route-preview.png"
    placement_plan_path = output_dir / "placement-plan.json"
    placement_preview_path = output_dir / "placement-preview.png"
    road_plan_path = output_dir / "road-plan.json"
    road_preview_path = output_dir / "road-preview.png"
    settlement_plan_path = output_dir / "settlement-plan.json"
    settlement_preview_path = output_dir / "settlement-preview.png"
    draft_mask_path = output_dir / "draft-mask.png"
    manifest_path = output_dir / "draft-manifest.json"

    world_plan = build_world_plan(config)
    write_project_review_page(config, review_page_path)
    write_world_plan(config, world_plan_path)
    transition_plan = build_transition_plan(world_plan)
    route_plan = build_route_plan(world_plan)
    placement_plan = build_placement_plan(world_plan, route_plan)
    road_plan = build_road_plan(route_plan, placement_plan)
    settlement_plan = build_settlement_plan(placement_plan, road_plan)
    write_transition_plan(world_plan, transition_plan_path)
    write_route_plan(world_plan, route_plan_path)
    write_placement_plan(world_plan, route_plan, placement_plan_path)
    write_road_plan(route_plan, placement_plan, road_plan_path)
    write_settlement_plan(placement_plan, road_plan, settlement_plan_path)
    write_material_profile(config.target_version, world_plan, transition_plan, road_plan, settlement_plan, material_profile_path)
    write_minecraft_export_request(config.target_version, world_plan, transition_plan, road_plan, settlement_plan, export_request_path)
    write_minecraft_chunk_plan(config.target_version, world_plan, transition_plan, road_plan, settlement_plan, chunk_plan_path)
    write_minecraft_block_fixture(config.target_version, world_plan, transition_plan, road_plan, settlement_plan, block_fixture_path)
    write_minecraft_nbt_fixture(config.target_version, world_plan, transition_plan, road_plan, settlement_plan, nbt_fixture_path)

    blocks_per_pixel = max(1, ceil(max(config.width, config.length) / max_draft_side))
    raster_width = ceil(config.width / blocks_per_pixel)
    raster_length = ceil(config.length / blocks_per_pixel)
    warnings = get_project_draft_warnings(
        world_width=config.width,
        world_length=config.length,
        raster_width=raster_width,
        raster_length=raster_length,
        blocks_per_pixel=blocks_per_pixel,
        regions=world_plan.regions,
    )

    draft_regions = _build_draft_regions(world_plan, blocks_per_pixel, raster_width, raster_length)
    pixels = _render_draft_mask(draft_regions, raster_width, raster_length)
    write_rgba_png(draft_mask_path, raster_width, raster_length, pixels)
    render_route_preview(
        route_plan,
        route_preview_path,
        raster_width=raster_width,
        raster_length=raster_length,
        blocks_per_pixel=blocks_per_pixel,
    )
    render_transition_preview(
        transition_plan,
        transition_preview_path,
        raster_width=raster_width,
        raster_length=raster_length,
        blocks_per_pixel=blocks_per_pixel,
    )
    render_placement_preview(
        route_plan,
        placement_plan,
        placement_preview_path,
        raster_width=raster_width,
        raster_length=raster_length,
        blocks_per_pixel=blocks_per_pixel,
    )
    render_road_preview(
        road_plan,
        placement_plan,
        road_preview_path,
        raster_width=raster_width,
        raster_length=raster_length,
        blocks_per_pixel=blocks_per_pixel,
    )
    render_settlement_preview(
        settlement_plan,
        settlement_preview_path,
        raster_width=raster_width,
        raster_length=raster_length,
        blocks_per_pixel=blocks_per_pixel,
    )

    manifest = {
        "schema": PROJECT_DRAFT_SCHEMA,
        "version": PROJECT_DRAFT_VERSION,
        "project": {
            "name": config.name,
            "targetVersion": config.target_version,
        },
        "world": {
            "width": config.width,
            "length": config.length,
        },
        "raster": {
            "width": raster_width,
            "length": raster_length,
            "blocksPerPixel": blocks_per_pixel,
            "maxDraftSide": max_draft_side,
        },
        "artifacts": {
            "reviewPage": review_page_path.name,
            "worldPlan": world_plan_path.name,
            "materialProfile": material_profile_path.name,
            "exportRequest": export_request_path.name,
            "chunkPlan": chunk_plan_path.name,
            "blockFixture": block_fixture_path.name,
            "nbtFixture": nbt_fixture_path.name,
            "transitionPlan": transition_plan_path.name,
            "transitionPreview": transition_preview_path.name,
            "routePlan": route_plan_path.name,
            "routePreview": route_preview_path.name,
            "placementPlan": placement_plan_path.name,
            "placementPreview": placement_preview_path.name,
            "roadPlan": road_plan_path.name,
            "roadPreview": road_preview_path.name,
            "settlementPlan": settlement_plan_path.name,
            "settlementPreview": settlement_preview_path.name,
            "draftMask": draft_mask_path.name,
        },
        "warnings": list(warnings),
        "regions": [
            {
                "title": region.title,
                "zone": region.zone_id,
                "shape": region.shape,
                "color": region.color,
                "bounds": {
                    "x": region.x,
                    "z": region.z,
                    "width": region.width,
                    "length": region.length,
                },
                "rasterBounds": {
                    "x": region.raster_x,
                    "z": region.raster_z,
                    "width": region.raster_width,
                    "length": region.raster_length,
                },
            }
            for region in draft_regions
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return ProjectDraftResult(
        output_dir=output_dir,
        review_page_path=review_page_path,
        world_plan_path=world_plan_path,
        material_profile_path=material_profile_path,
        export_request_path=export_request_path,
        chunk_plan_path=chunk_plan_path,
        block_fixture_path=block_fixture_path,
        nbt_fixture_path=nbt_fixture_path,
        transition_plan_path=transition_plan_path,
        transition_preview_path=transition_preview_path,
        route_plan_path=route_plan_path,
        route_preview_path=route_preview_path,
        placement_plan_path=placement_plan_path,
        placement_preview_path=placement_preview_path,
        road_plan_path=road_plan_path,
        road_preview_path=road_preview_path,
        settlement_plan_path=settlement_plan_path,
        settlement_preview_path=settlement_preview_path,
        draft_mask_path=draft_mask_path,
        manifest_path=manifest_path,
        world_width=config.width,
        world_length=config.length,
        raster_width=raster_width,
        raster_length=raster_length,
        blocks_per_pixel=blocks_per_pixel,
        warnings=warnings,
    )


def format_project_draft_result(result: ProjectDraftResult) -> str:
    return "\n".join(
        [
            f"Project draft: {result.output_dir}",
            f"- review page: {result.review_page_path.name}",
            f"- world plan: {result.world_plan_path.name}",
            f"- material profile: {result.material_profile_path.name}",
            f"- export request: {result.export_request_path.name}",
            f"- chunk plan: {result.chunk_plan_path.name}",
            f"- block fixture: {result.block_fixture_path.name}",
            f"- NBT fixture: {result.nbt_fixture_path.name}",
            f"- transition plan: {result.transition_plan_path.name}",
            f"- transition preview: {result.transition_preview_path.name}",
            f"- route plan: {result.route_plan_path.name}",
            f"- route preview: {result.route_preview_path.name}",
            f"- placement plan: {result.placement_plan_path.name}",
            f"- placement preview: {result.placement_preview_path.name}",
            f"- road plan: {result.road_plan_path.name}",
            f"- road preview: {result.road_preview_path.name}",
            f"- settlement plan: {result.settlement_plan_path.name}",
            f"- settlement preview: {result.settlement_preview_path.name}",
            f"- draft mask: {result.draft_mask_path.name}",
            f"- manifest: {result.manifest_path.name}",
            f"World size: {result.world_width} x {result.world_length}",
            f"Draft raster: {result.raster_width} x {result.raster_length}",
            f"Blocks per pixel: {result.blocks_per_pixel}",
            *[f"Warning: {warning}" for warning in result.warnings],
        ]
    )


def get_project_draft_warnings(
    *,
    world_width: int,
    world_length: int,
    raster_width: int,
    raster_length: int,
    blocks_per_pixel: int,
    regions: tuple[WorldPlanRegion, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    largest_side = max(world_width, world_length)
    region_count = len(regions)
    distinct_zone_families = {_infer_zone_id(region) for region in regions}

    if blocks_per_pixel > 1:
        warnings.append(
            f"Draft raster is scaled: 1 pixel represents {blocks_per_pixel} x {blocks_per_pixel} world blocks."
        )
    if blocks_per_pixel >= 16:
        warnings.append(
            "Large scale compression is active. Coastlines, roads, and small villages may be only approximate in the draft mask."
        )
    if min(raster_width, raster_length) < 128:
        warnings.append(
            "Draft raster is very small on at least one side. Region shapes may read clearly, but fine detail will not."
        )
    if largest_side >= 2048 and region_count < 4:
        warnings.append(
            f"Sparse world brief: this {world_width} x {world_length} world only defines {region_count} region(s). Add more regions before trusting roads, settlements, or story pacing."
        )
    if region_count >= 4 and len(distinct_zone_families) < 3:
        family_count = len(distinct_zone_families)
        family_label = "family" if family_count == 1 else "families"
        warnings.append(
            f"Weak zone variety: {region_count} region(s) collapse into only {family_count} zone {family_label}. Add stronger contrast before trusting the draft story flow."
        )
    return tuple(warnings)


def _build_draft_regions(
    world_plan: WorldPlan,
    blocks_per_pixel: int,
    raster_width: int,
    raster_length: int,
) -> tuple[DraftRegion, ...]:
    palette_by_zone = {zone.zone_id: zone.color for zone in DEFAULT_ZONE_PALETTE}
    draft_regions: list[DraftRegion] = []

    for region in world_plan.regions:
        zone_id = _infer_zone_id(region)
        color = palette_by_zone[zone_id]
        raster_x = max(0, region.x // blocks_per_pixel)
        raster_z = max(0, region.z // blocks_per_pixel)
        raster_end_x = min(raster_width, ceil((region.x + region.width) / blocks_per_pixel))
        raster_end_z = min(raster_length, ceil((region.z + region.length) / blocks_per_pixel))
        draft_regions.append(
            DraftRegion(
                title=region.title,
                zone_id=zone_id,
                shape=_infer_shape(zone_id),
                color=color.hex_rgb,
                x=region.x,
                z=region.z,
                width=region.width,
                length=region.length,
                raster_x=raster_x,
                raster_z=raster_z,
                raster_width=max(1, raster_end_x - raster_x),
                raster_length=max(1, raster_end_z - raster_z),
            )
        )

    return tuple(draft_regions)


def _render_draft_mask(
    draft_regions: tuple[DraftRegion, ...],
    raster_width: int,
    raster_length: int,
) -> tuple[tuple[tuple[int, int, int, int], ...], ...]:
    zone_colors = {zone.zone_id: zone.color.rgba for zone in DEFAULT_ZONE_PALETTE}
    base_color = zone_colors["land"]
    pixels = [[base_color for _x in range(raster_width)] for _z in range(raster_length)]

    for region in draft_regions:
        color = zone_colors[region.zone_id]
        max_z = min(raster_length, region.raster_z + region.raster_length)
        max_x = min(raster_width, region.raster_x + region.raster_width)
        for z in range(region.raster_z, max_z):
            row = pixels[z]
            local_z = _normalized_axis(z - region.raster_z, region.raster_length)
            for x in range(region.raster_x, max_x):
                local_x = _normalized_axis(x - region.raster_x, region.raster_width)
                if _shape_contains(region.shape, local_x, local_z):
                    row[x] = color

    return tuple(tuple(row) for row in pixels)


def _infer_zone_id(region: WorldPlanRegion) -> str:
    text = " ".join((region.kind, region.title, region.story_role, region.notes)).lower()
    tokens = set(re.findall(r"[a-z]+", text))
    for zone_id, keywords in _ZONE_KEYWORDS:
        if any(keyword in tokens for keyword in keywords):
            return zone_id
    return "land"


def _infer_shape(zone_id: str) -> str:
    if zone_id == "water":
        return "coast-band"
    if zone_id == "mountain":
        return "ridge-cap"
    if zone_id == "forest":
        return "oval-core"
    if zone_id in {"city", "port"}:
        return "settlement-core"
    if zone_id == "road":
        return "corridor"
    return "full-rect"


def _shape_contains(shape: str, local_x: float, local_z: float) -> bool:
    edge_distance = abs(local_x - 0.5) * 2.0

    if shape == "coast-band":
        threshold = 0.68 - 0.22 * (1.0 - edge_distance)
        return local_z >= threshold
    if shape == "ridge-cap":
        threshold = 0.32 + 0.22 * (1.0 - edge_distance)
        return local_z <= threshold
    if shape == "oval-core":
        return _ellipse_contains(local_x, local_z, center_x=0.5, center_z=0.52, radius_x=0.48, radius_z=0.34)
    if shape == "settlement-core":
        return _ellipse_contains(local_x, local_z, center_x=0.5, center_z=0.68, radius_x=0.42, radius_z=0.22)
    if shape == "corridor":
        return 0.42 <= local_z <= 0.58
    return True


def _ellipse_contains(
    local_x: float,
    local_z: float,
    *,
    center_x: float,
    center_z: float,
    radius_x: float,
    radius_z: float,
) -> bool:
    normalized_x = ((local_x - center_x) / radius_x) ** 2
    normalized_z = ((local_z - center_z) / radius_z) ** 2
    return normalized_x + normalized_z <= 1.0


def _normalized_axis(offset: int, span: int) -> float:
    if span <= 1:
        return 0.5
    return offset / (span - 1)
