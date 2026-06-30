from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

from titanforge.core.project import ProjectConfig
from titanforge.core.placement_plan import build_placement_plan
from titanforge.core.road_plan import build_road_plan
from titanforge.core.route_plan import build_route_plan
from titanforge.core.settlement_plan import build_settlement_plan
from titanforge.core.transition_plan import build_transition_plan
from titanforge.core.world_plan import WorldPlan, WorldPlanAnchor, WorldPlanRegion, build_world_plan
from titanforge.exporters.minecraft_12111_block_fixture import BlockFixtureCuboid, build_minecraft_block_fixture


ANVIL_REGION_SPIKE_SCHEMA = "titanforge.spike.anvil-region"
ANVIL_REGION_SPIKE_VERSION = 1
ANVIL_REGION_FILE_NAME = "r.0.0.mca"
ANVIL_DONOR_MODULE = "anvil"
ANVIL_DONOR_PACKAGE = "anvil-parser2"
ANVIL_DONOR_URL = "https://github.com/0xTiger/anvil-parser2"
ANVIL_DONOR_LICENSE = "MIT"
DEFAULT_SPIKE_MAX_SIDE = 512
MIN_SPIKE_SIDE = 16
MAX_SPIKE_SIDE = 512


class AnvilRegionSpikeError(RuntimeError):
    """Raised when the donor-backed Anvil region spike cannot run safely."""


@dataclass(frozen=True)
class AnvilBlockSample:
    x: int
    y: int
    z: int
    expected_block: str
    actual_block: str
    matches: bool


@dataclass(frozen=True)
class AnvilSampleWindow:
    origin_x: int
    origin_z: int
    sampled_width: int
    sampled_length: int
    cropped: bool
    focus_region_title: str | None


@dataclass(frozen=True)
class AnvilRegionSpikeResult:
    output_dir: Path
    manifest_path: Path
    readme_path: Path
    region_path: Path
    origin_x: int
    origin_z: int
    sampled_block_count: int
    sampled_cuboid_count: int
    sampled_width: int
    sampled_length: int
    cropped: bool
    focus_region_title: str | None
    warnings: tuple[str, ...]
    verification_samples: tuple[AnvilBlockSample, ...]


def write_anvil_region_spike(
    config: ProjectConfig,
    output_dir: Path,
    *,
    max_side: int = DEFAULT_SPIKE_MAX_SIDE,
    focus_region_title: str | None = None,
    anvil_module: Any | None = None,
) -> AnvilRegionSpikeResult:
    if not MIN_SPIKE_SIDE <= max_side <= MAX_SPIKE_SIDE:
        raise ValueError(f"max_side must be between {MIN_SPIKE_SIDE} and {MAX_SPIKE_SIDE}, got {max_side}.")
    if max_side % 16 != 0:
        raise ValueError(f"max_side must be divisible by 16 so the spike stays chunk-aligned, got {max_side}.")

    output_dir.mkdir(parents=True, exist_ok=True)
    region_dir = output_dir / "region"
    manifest_path = output_dir / "anvil-region-spike-manifest.json"
    readme_path = output_dir / "README.txt"
    region_path = region_dir / ANVIL_REGION_FILE_NAME

    world_plan = build_world_plan(config)
    transition_plan = build_transition_plan(world_plan)
    route_plan = build_route_plan(world_plan)
    placement_plan = build_placement_plan(world_plan, route_plan)
    road_plan = build_road_plan(route_plan, placement_plan)
    settlement_plan = build_settlement_plan(placement_plan, road_plan)
    fixture = build_minecraft_block_fixture(
        config.target_version,
        world_plan,
        transition_plan,
        road_plan,
        settlement_plan,
    )

    if not fixture.supported:
        raise AnvilRegionSpikeError(
            f"No supported 1.21.11 block fixture is available for requested target {config.target_version}."
        )

    sample_window = _build_sample_window(world_plan, max_side=max_side, focus_region_title=focus_region_title)
    sampled_cuboids = _clip_fixture_to_window(
        fixture.cuboids,
        origin_x=sample_window.origin_x,
        origin_z=sample_window.origin_z,
        sampled_width=sample_window.sampled_width,
        sampled_length=sample_window.sampled_length,
    )
    if not sampled_cuboids:
        raise AnvilRegionSpikeError("The sampled window did not contain any block cuboids to export.")

    warnings: list[str] = []
    if sample_window.cropped:
        warnings.append(
            f"World {config.width} x {config.length} was clipped to a {sample_window.sampled_width} x {sample_window.sampled_length} sampled window "
            "so this donor-backed spike stays inside one safe region file."
        )
    if sample_window.focus_region_title:
        warnings.append(
            f'The sampled window was recentered around the "{sample_window.focus_region_title}" story region instead of staying at world origin.'
        )

    sampled_block_count = sum(
        cuboid.width * cuboid.height * cuboid.length
        for cuboid in sampled_cuboids
    )
    warnings.append(
        "This is an isolated donor-backed region spike. It proves one real .mca write/read path, not a production-ready world export."
    )

    module = anvil_module if anvil_module is not None else _load_anvil_module()
    _write_region_file(module, sampled_cuboids, region_path)
    verification_samples = _verify_region_file(module, region_path, sampled_cuboids)

    donor_version = _get_anvil_donor_version()
    manifest = {
        "schema": ANVIL_REGION_SPIKE_SCHEMA,
        "version": ANVIL_REGION_SPIKE_VERSION,
        "project": {
            "name": config.name,
            "targetVersion": config.target_version,
            "worldWidth": config.width,
            "worldLength": config.length,
        },
        "donor": {
            "package": ANVIL_DONOR_PACKAGE,
            "module": ANVIL_DONOR_MODULE,
            "version": donor_version,
            "license": ANVIL_DONOR_LICENSE,
            "url": ANVIL_DONOR_URL,
        },
        "artifacts": {
            "regionFile": str(region_path.relative_to(output_dir)),
            "readme": readme_path.name,
        },
        "sampleWindow": {
            "origin": {"x": sample_window.origin_x, "z": sample_window.origin_z},
            "size": {"width": sample_window.sampled_width, "length": sample_window.sampled_length},
            "cropped": sample_window.cropped,
            "focusRegion": sample_window.focus_region_title,
        },
        "export": {
            "sampledCuboids": len(sampled_cuboids),
            "sampledBlockCount": sampled_block_count,
        },
        "verification": {
            "sampleCount": len(verification_samples),
            "allMatched": all(sample.matches for sample in verification_samples),
            "samples": [
                {
                    "x": sample.x,
                    "y": sample.y,
                    "z": sample.z,
                    "expectedBlock": sample.expected_block,
                    "actualBlock": sample.actual_block,
                    "matches": sample.matches,
                }
                for sample in verification_samples
            ],
        },
        "warnings": warnings,
    }

    region_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme_path.write_text("\n".join(_build_readme_lines(config, sample_window, donor_version)) + "\n", encoding="utf-8")

    return AnvilRegionSpikeResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        readme_path=readme_path,
        region_path=region_path,
        origin_x=sample_window.origin_x,
        origin_z=sample_window.origin_z,
        sampled_block_count=sampled_block_count,
        sampled_cuboid_count=len(sampled_cuboids),
        sampled_width=sample_window.sampled_width,
        sampled_length=sample_window.sampled_length,
        cropped=sample_window.cropped,
        focus_region_title=sample_window.focus_region_title,
        warnings=tuple(warnings),
        verification_samples=verification_samples,
    )


def format_anvil_region_spike_result(result: AnvilRegionSpikeResult) -> str:
    lines = [
        f"Anvil region spike: {result.output_dir}",
        f"- region file: {result.region_path.name}",
        f"- manifest: {result.manifest_path.name}",
        f"- readme: {result.readme_path.name}",
        f"- sampled window: {result.sampled_width} x {result.sampled_length}",
        f"- sampled origin: x={result.origin_x} z={result.origin_z}",
        f"- sampled cuboids: {result.sampled_cuboid_count}",
        f"- sampled blocks: {result.sampled_block_count}",
        f"- verification samples: {len(result.verification_samples)}",
    ]
    if result.focus_region_title:
        lines.append(f"- focus region: {result.focus_region_title}")
    for warning in result.warnings:
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)


def _build_readme_lines(
    config: ProjectConfig,
    sample_window: AnvilSampleWindow,
    donor_version: str,
) -> tuple[str, ...]:
    crop_line = (
        f"The original {config.width} x {config.length} world was clipped to a sampled {sample_window.sampled_width} x {sample_window.sampled_length} window."
        if sample_window.cropped
        else "The sampled window matches the logical world size."
    )
    focus_line = (
        f'- Focus region: "{sample_window.focus_region_title}"'
        if sample_window.focus_region_title
        else "- Focus region: world origin sample"
    )
    return (
        "TitanForge donor-backed Anvil region spike",
        "",
        "Purpose:",
        "- Prove one narrow write/read path for a real Minecraft region artifact.",
        "- Keep donor code out of TitanForge core planning modules.",
        "",
        "Donor:",
        f"- Package: {ANVIL_DONOR_PACKAGE}",
        f"- Version: {donor_version}",
        f"- License: {ANVIL_DONOR_LICENSE}",
        f"- URL: {ANVIL_DONOR_URL}",
        "",
        "Output:",
        f"- Region file: region\\{ANVIL_REGION_FILE_NAME}",
        f"- Sample window: {sample_window.sampled_width} x {sample_window.sampled_length} blocks",
        f"- Sample origin inside the logical world: x={sample_window.origin_x}, z={sample_window.origin_z}",
        focus_line,
        f"- {crop_line}",
        "",
        "Limits:",
        "- This is not a complete world save.",
        "- It intentionally stays chunk-aligned and within one safe region file.",
        "- Use it to validate exporter direction before attempting full world writing.",
    )


def _clip_fixture_to_window(
    cuboids: tuple[BlockFixtureCuboid, ...],
    *,
    origin_x: int,
    origin_z: int,
    sampled_width: int,
    sampled_length: int,
) -> tuple[BlockFixtureCuboid, ...]:
    clipped: list[BlockFixtureCuboid] = []
    for cuboid in cuboids:
        start_x = max(origin_x, cuboid.x)
        start_z = max(origin_z, cuboid.z)
        end_x = min(origin_x + sampled_width, cuboid.x + cuboid.width)
        end_z = min(origin_z + sampled_length, cuboid.z + cuboid.length)
        if start_x >= end_x or start_z >= end_z:
            continue
        clipped.append(
            BlockFixtureCuboid(
                id=cuboid.id,
                source_type=cuboid.source_type,
                operation=cuboid.operation,
                x=start_x - origin_x,
                y=cuboid.y,
                z=start_z - origin_z,
                width=end_x - start_x,
                height=cuboid.height,
                length=end_z - start_z,
                primary_block=cuboid.primary_block,
                accent_blocks=cuboid.accent_blocks,
            )
        )
    return tuple(clipped)


def _write_region_file(anvil_module: Any, cuboids: tuple[BlockFixtureCuboid, ...], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    region = anvil_module.EmptyRegion(0, 0)
    for cuboid in cuboids:
        block = _block_from_name(anvil_module, cuboid.primary_block)
        for y in range(cuboid.y, cuboid.y + cuboid.height):
            for z in range(cuboid.z, cuboid.z + cuboid.length):
                for x in range(cuboid.x, cuboid.x + cuboid.width):
                    region.set_block(block, x, y, z)
    region.save(str(output_path))


def _verify_region_file(
    anvil_module: Any,
    region_path: Path,
    cuboids: tuple[BlockFixtureCuboid, ...],
) -> tuple[AnvilBlockSample, ...]:
    region = anvil_module.Region.from_file(str(region_path))
    samples: list[AnvilBlockSample] = []
    for cuboid in cuboids[:12]:
        for x, y, z in _cuboid_probe_points(cuboid):
            chunk = anvil_module.Chunk.from_region(region, x // 16, z // 16)
            actual = chunk.get_block(x % 16, y, z % 16)
            actual_name = _format_block_state(actual.namespace, actual.id, actual.properties)
            expected_name = _normalize_block_name(cuboid.primary_block)
            samples.append(
                AnvilBlockSample(
                    x=x,
                    y=y,
                    z=z,
                    expected_block=expected_name,
                    actual_block=actual_name,
                    matches=actual_name == expected_name,
                )
            )
    return tuple(samples)


def _cuboid_probe_points(cuboid: BlockFixtureCuboid) -> tuple[tuple[int, int, int], ...]:
    end_x = cuboid.x + cuboid.width - 1
    end_y = cuboid.y + cuboid.height - 1
    end_z = cuboid.z + cuboid.length - 1
    center_x = cuboid.x + (cuboid.width - 1) // 2
    center_z = cuboid.z + (cuboid.length - 1) // 2
    points = [
        (cuboid.x, cuboid.y, cuboid.z),
        (end_x, end_y, end_z),
        (center_x, cuboid.y, center_z),
    ]
    unique_points: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for point in points:
        if point not in seen:
            seen.add(point)
            unique_points.append(point)
    return tuple(unique_points)


def _block_from_name(anvil_module: Any, block_name: str) -> Any:
    namespace, block_id, properties = _parse_block_state(block_name)
    return anvil_module.Block(namespace, block_id, properties)


def _parse_block_state(block_name: str) -> tuple[str, str, dict[str, str]]:
    raw_name, separator, raw_properties = block_name.partition("[")
    qualified_name = raw_name if ":" in raw_name else f"minecraft:{raw_name}"
    namespace, _, block_id = qualified_name.partition(":")
    properties: dict[str, str] = {}
    if separator:
        for entry in raw_properties.rstrip("]").split(","):
            key, _, value = entry.partition("=")
            if key and value:
                properties[key] = value
    return namespace, block_id, properties


def _format_block_state(namespace: str, block_id: str, properties: dict[str, str] | None) -> str:
    qualified_name = f"{namespace}:{block_id}"
    if not properties:
        return qualified_name
    properties_text = ",".join(f"{key}={value}" for key, value in sorted(properties.items()))
    return f"{qualified_name}[{properties_text}]"


def _normalize_block_name(block_name: str) -> str:
    namespace, block_id, properties = _parse_block_state(block_name)
    return _format_block_state(namespace, block_id, properties)


def _load_anvil_module() -> Any:
    try:
        return importlib.import_module(ANVIL_DONOR_MODULE)
    except ImportError as exc:
        raise AnvilRegionSpikeError(
            "anvil-parser2 is not installed. Run `py -3.11 -m pip install -e .[donor-spikes]` before using anvil-region-spike."
        ) from exc


def _get_anvil_donor_version() -> str:
    try:
        return importlib.metadata.version(ANVIL_DONOR_PACKAGE)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _build_sample_window(
    world_plan: WorldPlan,
    *,
    max_side: int,
    focus_region_title: str | None,
) -> AnvilSampleWindow:
    sampled_width = min(world_plan.width, max_side)
    sampled_length = min(world_plan.length, max_side)
    cropped = world_plan.width > sampled_width or world_plan.length > sampled_length
    focus_region = _resolve_focus_region(world_plan, focus_region_title)
    if focus_region is None:
        return AnvilSampleWindow(
            origin_x=0,
            origin_z=0,
            sampled_width=sampled_width,
            sampled_length=sampled_length,
            cropped=cropped,
            focus_region_title=None,
        )

    focus_anchor = _pick_focus_anchor(focus_region)
    origin_x = _align_sample_origin(focus_anchor.x - sampled_width // 2, world_plan.width, sampled_width)
    origin_z = _align_sample_origin(focus_anchor.z - sampled_length // 2, world_plan.length, sampled_length)
    return AnvilSampleWindow(
        origin_x=origin_x,
        origin_z=origin_z,
        sampled_width=sampled_width,
        sampled_length=sampled_length,
        cropped=cropped,
        focus_region_title=focus_region.title,
    )


def _resolve_focus_region(world_plan: WorldPlan, focus_region_title: str | None) -> WorldPlanRegion | None:
    if focus_region_title is None:
        return None
    normalized = focus_region_title.strip().casefold()
    for region in world_plan.regions:
        if region.title.casefold() == normalized:
            return region
    available = ", ".join(region.title for region in world_plan.regions) or "<none>"
    raise AnvilRegionSpikeError(
        f'Unknown --focus-region "{focus_region_title}". Choose one of: {available}.'
    )


def _pick_focus_anchor(region: WorldPlanRegion) -> WorldPlanAnchor:
    preferred_anchor_ids = ("arrival", "center", "focus", "shoreline", "forest-core", "ridge-vista", "entry")
    for anchor_id in preferred_anchor_ids:
        for anchor in region.anchors:
            if anchor.id == anchor_id:
                return anchor
    if region.anchors:
        return region.anchors[0]
    return WorldPlanAnchor(
        id="region-center",
        role="Fallback region center",
        x=region.x + region.width // 2,
        z=region.z + region.length // 2,
    )


def _align_sample_origin(target: int, logical_side: int, sample_side: int) -> int:
    max_origin = max(0, logical_side - sample_side)
    clamped = min(max(0, target), max_origin)
    aligned = clamped - (clamped % 16)
    max_aligned = max_origin - (max_origin % 16)
    return min(aligned, max_aligned)
