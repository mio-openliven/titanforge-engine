from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from titanforge.core.project import ProjectConfig, ProjectRegion

PROJECT_TEMPLATE_MIN_SIDE = 64
PROJECT_TEMPLATE_MAX_SIDE = 32000
PROJECT_TEMPLATE_PRESET_CATALOG_SCHEMA = "titanforge.project-template-preset-catalog"
PROJECT_TEMPLATE_PRESET_CATALOG_VERSION = 1
DEFAULT_TEMPLATE_PIPELINE = (
    "load_masks",
    "resolve_layout",
    "terrain_pass",
    "preview",
    "export",
)


class ProjectTemplateError(ValueError):
    """Raised when a starter project template request is invalid."""


@dataclass(frozen=True)
class ProjectTemplatePreset:
    premise: str
    player_experience: str
    regions: tuple[ProjectRegion, ...]


@dataclass(frozen=True)
class ProjectTemplateResult:
    project_dir: Path
    config_path: Path
    suggested_output_dir: Path
    preset_name: str
    config: ProjectConfig


@dataclass(frozen=True)
class WorldScaleGuidance:
    label: str
    summary: str
    planning_note: str


PROJECT_TEMPLATE_PRESETS: dict[str, ProjectTemplatePreset] = {
    "coastal-valley": ProjectTemplatePreset(
        premise="A cinematic coast-to-mountain story space where the player starts near human safety and moves toward older, stranger ground.",
        player_experience="The player should feel grounded at first, then curious, then increasingly small inside a wider natural and story-driven world.",
        regions=(
            ProjectRegion(
                title="Harbor Town",
                kind="city",
                story_role="safe arrival and logistics hub",
                mood="busy, human, believable",
                coverage_hint="15%",
                notes="Acts as the first readable anchor for players, crews, and story staging.",
            ),
            ProjectRegion(
                title="Salt Coast",
                kind="sea",
                story_role="weather border and travel horizon",
                mood="open, windy, cinematic",
                coverage_hint="20%",
                notes="Supports boats, fog, shore shots, and a strong sense of edge.",
            ),
            ProjectRegion(
                title="Old Pine Forest",
                kind="forest",
                story_role="mystery buffer between settlement and danger",
                mood="quiet, dense, unsettling",
                coverage_hint="25%",
                notes="A good place for getting lost, hiding clues, and staging slower exploration.",
            ),
            ProjectRegion(
                title="River Village",
                kind="village",
                story_role="secondary human anchor away from the main city",
                mood="fragile, warm, isolated",
                coverage_hint="15%",
                notes="Makes the world feel lived in instead of only monumental.",
            ),
            ProjectRegion(
                title="Broken Ridge",
                kind="mountains",
                story_role="late reveal and high-visibility payoff zone",
                mood="cold, ancient, exposed",
                coverage_hint="25%",
                notes="Holds views, ruins, and the strongest sense of forgotten history.",
            ),
        ),
    ),
    "frontier-basin": ProjectTemplatePreset(
        premise="A broad inland basin where farms, marsh, timber routes, and a defensive ridge together tell a frontier survival story.",
        player_experience="The player should feel like civilization is trying to hold the land together while wilderness keeps pressing in.",
        regions=(
            ProjectRegion(
                title="Gate Town",
                kind="town",
                story_role="arrival market and supply checkpoint",
                mood="muddy, active, practical",
                coverage_hint="18%",
                notes="A first touchpoint for caravans, wagons, and grounded story scenes.",
            ),
            ProjectRegion(
                title="Low Marsh",
                kind="swamp",
                story_role="detour pressure and mood contrast",
                mood="wet, uneasy, slow",
                coverage_hint="18%",
                notes="Adds traversal friction and uneasy atmosphere near the basin floor.",
            ),
            ProjectRegion(
                title="Far Grain Plain",
                kind="plains",
                story_role="breathing room and scale reveal",
                mood="open, seasonal, vulnerable",
                coverage_hint="24%",
                notes="Useful for long travel shots and showing what the settlements are trying to protect.",
            ),
            ProjectRegion(
                title="Timber Forest",
                kind="forest",
                story_role="resource zone and ambush cover",
                mood="shadowed, practical, watchful",
                coverage_hint="20%",
                notes="Feeds roads and construction while keeping tension near the routes.",
            ),
            ProjectRegion(
                title="Watch Ridge",
                kind="mountains",
                story_role="defensive overlook and late reveal",
                mood="hard, windswept, disciplined",
                coverage_hint="20%",
                notes="Supports forts, lookouts, and the main basin overview shot.",
            ),
        ),
    ),
    "island-kingdom": ProjectTemplatePreset(
        premise="A layered island setting with one strong capital, broken shorelines, and interior wild zones that hold older secrets than the ruling city admits.",
        player_experience="The player should feel the tension between authority on the coast and older, less controlled forces inland.",
        regions=(
            ProjectRegion(
                title="Crown Harbor",
                kind="city",
                story_role="official arrival and power center",
                mood="grand, ordered, ceremonial",
                coverage_hint="20%",
                notes="Supports markets, docks, walls, and strong first-impression staging.",
            ),
            ProjectRegion(
                title="Stormwater Shore",
                kind="sea",
                story_role="island edge and weather source",
                mood="restless, loud, cinematic",
                coverage_hint="20%",
                notes="Creates drama through cliffs, surf, and exposed approaches.",
            ),
            ProjectRegion(
                title="Interior Canopy",
                kind="forest",
                story_role="concealment and myth layer",
                mood="humid, ancient, immersive",
                coverage_hint="25%",
                notes="A place for temples, hidden routes, and slower environmental storytelling.",
            ),
            ProjectRegion(
                title="High Shrine Steps",
                kind="mountains",
                story_role="pilgrimage route and payoff vista",
                mood="steep, sacred, exposed",
                coverage_hint="20%",
                notes="Lets elevation become part of the story instead of only a backdrop.",
            ),
            ProjectRegion(
                title="Outer Hamlet",
                kind="village",
                story_role="civilian contrast away from the capital",
                mood="humble, loyal, weathered",
                coverage_hint="15%",
                notes="Helps the island feel inhabited beyond the showcase city.",
            ),
        ),
    ),
}


def list_project_template_presets() -> tuple[str, ...]:
    return tuple(PROJECT_TEMPLATE_PRESETS.keys())


def build_project_template_preset_catalog_data() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for preset_name in list_project_template_presets():
        preset = PROJECT_TEMPLATE_PRESETS[preset_name]
        items.append(
            {
                "id": preset_name,
                "story": preset.premise,
                "playerFeeling": preset.player_experience,
                "keyRegions": [region.title for region in preset.regions],
            }
        )
    return items


def build_project_template_preset_catalog_payload() -> dict[str, object]:
    return {
        "schema": PROJECT_TEMPLATE_PRESET_CATALOG_SCHEMA,
        "version": PROJECT_TEMPLATE_PRESET_CATALOG_VERSION,
        "presets": build_project_template_preset_catalog_data(),
        "usage": {
            "nextCommand": "py -3.11 -m titanforge init-project <folder> --preset <preset-name>",
            "safeWorldSize": {
                "minBlocks": PROJECT_TEMPLATE_MIN_SIDE,
                "maxBlocks": PROJECT_TEMPLATE_MAX_SIDE,
            },
        },
    }


def format_project_template_preset_catalog() -> str:
    lines = ["TitanForge starter presets:"]
    for item in build_project_template_preset_catalog_data():
        region_titles = tuple(str(title) for title in item["keyRegions"])
        region_lineup = _format_region_lineup(region_titles)
        lines.extend(
            (
                f"- {item['id']}",
                f"  story: {item['story']}",
                f"  feeling: {item['playerFeeling']}",
                f"  regions: {region_lineup}",
            )
        )
    lines.append("Use one with: py -3.11 -m titanforge init-project <folder> --preset <preset-name>")
    return "\n".join(lines)


def describe_world_scale(width: int, length: int) -> WorldScaleGuidance:
    max_side = max(width, length)
    if max_side <= 512:
        return WorldScaleGuidance(
            label="Pocket scene",
            summary="Best for one strong set piece, one village pocket, or a tight prototype.",
            planning_note="At this size the draft preview stays fairly close to the intended block footprint.",
        )
    if max_side <= 2048:
        return WorldScaleGuidance(
            label="Local district",
            summary="Good for one town plus nearby coast, forest, ridge, or harbor.",
            planning_note="This size is still comfortable for local travel beats and direct visual landmarks.",
        )
    if max_side <= 8192:
        return WorldScaleGuidance(
            label="Regional journey",
            summary="Good for multiple story zones, visible travel, and a fuller sense of surrounding land.",
            planning_note="The draft starts getting more abstract, so prefer broad composition decisions before tiny detail promises.",
        )
    return WorldScaleGuidance(
        label="Long-travel world",
        summary="Best for cinematic countries, huge coastlines, or long overland journeys between major anchors.",
        planning_note="The draft preview stays intentionally abstract here, so judge composition first and save fine detail for later passes.",
    )


def build_project_template_config(
    project_name: str | None,
    width: int,
    length: int,
    preset_name: str,
    *,
    target_version: str = "1.21.11",
) -> ProjectConfig:
    if preset_name not in PROJECT_TEMPLATE_PRESETS:
        supported = ", ".join(list_project_template_presets())
        raise ProjectTemplateError(f"Unknown preset '{preset_name}'. Choose one of: {supported}.")

    _validate_project_side("width", width)
    _validate_project_side("length", length)

    preset = PROJECT_TEMPLATE_PRESETS[preset_name]
    return ProjectConfig(
        name=_normalize_project_name(project_name),
        target_version=target_version,
        width=width,
        length=length,
        premise=preset.premise,
        player_experience=preset.player_experience,
        regions=preset.regions,
        pipeline=DEFAULT_TEMPLATE_PIPELINE,
    )


def write_project_template(
    project_dir: Path,
    project_name: str | None,
    width: int,
    length: int,
    preset_name: str,
    *,
    target_version: str = "1.21.11",
) -> ProjectTemplateResult:
    project_dir.mkdir(parents=True, exist_ok=True)
    config_path = project_dir / "titanforge.toml"
    if config_path.exists():
        raise FileExistsError(f"Starter config already exists: {config_path}")

    config = build_project_template_config(
        project_name,
        width,
        length,
        preset_name,
        target_version=target_version,
    )
    config_path.write_text(render_project_template_toml(config), encoding="utf-8")

    return ProjectTemplateResult(
        project_dir=project_dir,
        config_path=config_path,
        suggested_output_dir=project_dir / "first-map",
        preset_name=preset_name,
        config=config,
    )


def format_project_template_result(result: ProjectTemplateResult) -> str:
    scale = describe_world_scale(result.config.width, result.config.length)
    region_lineup = _format_region_lineup(tuple(region.title for region in result.config.regions))
    next_command = (
        f'py -3.11 -m titanforge project-location "{result.config_path}" '
        f'"{result.suggested_output_dir}" --use-cleanup-for-heightmap'
    )
    return "\n".join(
        (
            f"Project template: {result.config_path}",
            f"Preset: {result.preset_name}",
            f"Target: {result.config.target_version}",
            f"World size: {result.config.width} x {result.config.length}",
            f"Allowed size: {PROJECT_TEMPLATE_MIN_SIDE} .. {PROJECT_TEMPLATE_MAX_SIDE} blocks",
            f"World scale: {scale.label}",
            f"Scale use: {scale.summary}",
            f"Preset story: {result.config.premise}",
            f"Player feeling: {result.config.player_experience}",
            f"Key regions: {region_lineup}",
            "Change later: edit width and length in titanforge.toml, then run project-location again.",
            scale.planning_note,
            "Large worlds still use a smaller draft raster during planning; later output shows the blocks-per-pixel scale.",
            "Next:",
            f"- review and adjust: {result.config_path.name}",
            f"- build first map: {next_command}",
        )
    )


def render_project_template_toml(config: ProjectConfig) -> str:
    lines = [
        "[project]",
        f'name = {_toml_string(config.name)}',
        f'target_version = {_toml_string(config.target_version)}',
        "",
        "[world]",
        f"width = {config.width}",
        f"length = {config.length}",
        "",
        "[creative]",
        f'premise = {_toml_string(config.premise)}',
        f'player_experience = {_toml_string(config.player_experience)}',
        "",
    ]

    for region in config.regions:
        lines.extend(
            (
                "[[regions]]",
                f'title = {_toml_string(region.title)}',
                f'kind = {_toml_string(region.kind)}',
                f'story_role = {_toml_string(region.story_role)}',
                f'mood = {_toml_string(region.mood)}',
                f'coverage_hint = {_toml_string(region.coverage_hint)}',
                f'notes = {_toml_string(region.notes)}',
                "",
            )
        )

    lines.extend(
        (
            "[pipeline]",
            "stages = [",
            *(f"    {_toml_string(stage)}," for stage in config.pipeline),
            "]",
            "",
        )
    )
    return "\n".join(lines)


def _validate_project_side(label: str, value: int) -> None:
    if value < PROJECT_TEMPLATE_MIN_SIDE or value > PROJECT_TEMPLATE_MAX_SIDE:
        raise ProjectTemplateError(
            f"{label} must stay between {PROJECT_TEMPLATE_MIN_SIDE} and {PROJECT_TEMPLATE_MAX_SIDE} blocks, got {value}."
        )


def _normalize_project_name(project_name: str | None) -> str:
    if project_name is None or not project_name.strip():
        return "New TitanForge World"
    return project_name.strip()


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _format_region_lineup(region_titles: tuple[str, ...], *, limit: int = 3) -> str:
    if not region_titles:
        return "No starter regions."
    if len(region_titles) <= limit:
        return ", ".join(region_titles)
    visible = ", ".join(region_titles[:limit])
    return f"{visible}, +{len(region_titles) - limit} more"
