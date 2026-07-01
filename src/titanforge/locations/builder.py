from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil

from titanforge.layouts.mask_layout import write_mask_layout
from titanforge.locations.review_page import write_location_review_page
from titanforge.masks.coastline import render_coastline_smoothing_preview
from titanforge.masks.cleanup import render_mask_cleanup_preview
from titanforge.masks.demo import generate_demo_mask
from titanforge.masks.png import read_png
from titanforge.preview.mask_preview import render_mask_preview
from titanforge.terrain.color_preview import render_terrain_color_preview
from titanforge.terrain.heightmap_preview import render_heightmap_preview
from titanforge.validation.layout_report import write_layout_validation_report


@dataclass(frozen=True)
class LocationBuildResult:
    output_dir: Path
    mask_path: Path
    mask_preview_path: Path
    cleanup_preview_path: Path
    coastline_smoothing_preview_path: Path
    layout_path: Path
    terrain_color_preview_path: Path
    heightmap_path: Path
    heightmap_source_path: Path
    report_path: Path
    review_page_path: Path
    manifest_path: Path
    warnings: int
    errors: int


def build_location_pack(
    output_dir: Path,
    input_mask: Path | None = None,
    *,
    demo: bool = False,
    width: int = 128,
    height: int = 128,
    use_cleanup_for_heightmap: bool = False,
    source_mode_override: str | None = None,
    draft_artifacts: tuple[tuple[str, str], ...] = (),
    project_root_artifacts: tuple[tuple[str, str], ...] = (),
    draft_fixture_summary: dict[str, object] | None = None,
    draft_fixture_commands: tuple[str, ...] = (),
) -> LocationBuildResult:
    if input_mask is None and not demo:
        demo = True

    output_dir.mkdir(parents=True, exist_ok=True)

    mask_path = output_dir / "mask.png"
    mask_preview_path = output_dir / "mask-preview.png"
    cleanup_preview_path = output_dir / "mask-cleanup-preview.png"
    coastline_smoothing_preview_path = output_dir / "coastline-smoothing-preview.png"
    layout_path = output_dir / "layout.json"
    terrain_color_preview_path = output_dir / "terrain-color-preview.png"
    heightmap_path = output_dir / "heightmap-preview.png"
    report_path = output_dir / "report.txt"
    review_page_path = output_dir / "review.html"
    manifest_path = output_dir / "manifest.json"

    if demo:
        generate_demo_mask(mask_path, width=width, height=height)
        source_mode = "demo"
    else:
        if input_mask is None:
            raise ValueError("input_mask is required when demo mode is disabled.")
        _copy_input_mask(input_mask, mask_path)
        source_mode = "input"
    if source_mode_override is not None:
        source_mode = source_mode_override

    mask_image = read_png(mask_path)
    render_mask_preview(mask_path, mask_preview_path, image=mask_image)
    render_mask_cleanup_preview(mask_path, cleanup_preview_path, image=mask_image)
    render_coastline_smoothing_preview(mask_path, coastline_smoothing_preview_path, image=mask_image)
    write_mask_layout(mask_path, layout_path, image=mask_image)
    heightmap_source_path = cleanup_preview_path if use_cleanup_for_heightmap else mask_path
    render_terrain_color_preview(
        layout_path,
        terrain_color_preview_path,
        mask_override_path=heightmap_source_path if use_cleanup_for_heightmap else None,
        mask_image=None if use_cleanup_for_heightmap else mask_image,
    )
    render_heightmap_preview(
        layout_path,
        heightmap_path,
        mask_override_path=heightmap_source_path if use_cleanup_for_heightmap else None,
        mask_image=None if use_cleanup_for_heightmap else mask_image,
    )
    validation = write_layout_validation_report(layout_path, report_path)
    report_text = report_path.read_text(encoding="utf-8")

    manifest = {
        "schema": "titanforge.location-pack",
        "version": 1,
        "sourceMode": source_mode,
        "artifacts": {
            "mask": mask_path.name,
            "maskPreview": mask_preview_path.name,
            "maskCleanupPreview": cleanup_preview_path.name,
            "coastlineSmoothingPreview": coastline_smoothing_preview_path.name,
            "layout": layout_path.name,
            "terrainColorPreview": terrain_color_preview_path.name,
            "heightmapPreview": heightmap_path.name,
            "report": report_path.name,
            "reviewPage": review_page_path.name,
        },
        "terrain": {
            "heightmapSource": heightmap_source_path.name,
            "cleanupApplied": use_cleanup_for_heightmap,
        },
        "validation": {
            "errors": validation.error_count,
            "warnings": validation.warning_count,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_location_review_page(
        output_dir,
        pack_name=output_dir.name,
        source_mode=source_mode,
        validation_errors=validation.error_count,
        validation_warnings=validation.warning_count,
        cleanup_applied=use_cleanup_for_heightmap,
        heightmap_source=heightmap_source_path.name,
        report_text=report_text,
        draft_artifacts=draft_artifacts,
        project_root_artifacts=project_root_artifacts,
        draft_fixture_summary=draft_fixture_summary,
        draft_fixture_commands=draft_fixture_commands,
    )

    return LocationBuildResult(
        output_dir=output_dir,
        mask_path=mask_path,
        mask_preview_path=mask_preview_path,
        cleanup_preview_path=cleanup_preview_path,
        coastline_smoothing_preview_path=coastline_smoothing_preview_path,
        layout_path=layout_path,
        terrain_color_preview_path=terrain_color_preview_path,
        heightmap_path=heightmap_path,
        heightmap_source_path=heightmap_source_path,
        report_path=report_path,
        review_page_path=review_page_path,
        manifest_path=manifest_path,
        warnings=validation.warning_count,
        errors=validation.error_count,
    )


def format_location_build_result(result: LocationBuildResult) -> str:
    return "\n".join(
        [
            f"Location pack: {result.output_dir}",
            f"- mask: {result.mask_path.name}",
            f"- preview: {result.mask_preview_path.name}",
            f"- cleanup preview: {result.cleanup_preview_path.name}",
            f"- coastline smoothing preview: {result.coastline_smoothing_preview_path.name}",
            f"- layout: {result.layout_path.name}",
            f"- terrain color preview: {result.terrain_color_preview_path.name}",
            f"- heightmap: {result.heightmap_path.name}",
            f"- heightmap source: {result.heightmap_source_path.name}",
            f"- report: {result.report_path.name}",
            f"- review page: {result.review_page_path.name}",
            f"- manifest: {result.manifest_path.name}",
            f"Validation: {result.errors} errors, {result.warnings} warnings",
        ]
    )


def _copy_input_mask(input_mask: Path, mask_path: Path) -> None:
    resolved_input = input_mask.resolve()
    resolved_output = mask_path.resolve()
    if resolved_input == resolved_output:
        return
    shutil.copyfile(resolved_input, resolved_output)
