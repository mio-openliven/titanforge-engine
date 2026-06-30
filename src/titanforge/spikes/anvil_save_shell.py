from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.project import ProjectConfig
from titanforge.spikes.anvil_region import (
    ANVIL_DONOR_LICENSE,
    ANVIL_DONOR_PACKAGE,
    ANVIL_DONOR_URL,
    ANVIL_REGION_FILE_NAME,
    DEFAULT_SPIKE_MAX_SIDE,
    AnvilRegionSpikeResult,
    write_anvil_region_spike,
)


ANVIL_SAVE_SHELL_SCHEMA = "titanforge.spike.anvil-save-shell"
ANVIL_SAVE_SHELL_VERSION = 1


@dataclass(frozen=True)
class AnvilSaveShellResult:
    output_dir: Path
    manifest_path: Path
    readme_path: Path
    shell_dir: Path
    shell_region_path: Path
    shell_spike_manifest_path: Path
    shell_spike_readme_path: Path
    sampled_width: int
    sampled_length: int
    cropped: bool
    warnings: tuple[str, ...]


def write_anvil_save_shell(
    config: ProjectConfig,
    output_dir: Path,
    *,
    max_side: int = DEFAULT_SPIKE_MAX_SIDE,
    anvil_module: Any | None = None,
) -> AnvilSaveShellResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    shell_dir = output_dir / "save-shell"
    manifest_path = output_dir / "anvil-save-shell-manifest.json"
    readme_path = output_dir / "README.txt"

    spike_result = write_anvil_region_spike(config, shell_dir, max_side=max_side, anvil_module=anvil_module)
    shell_region_path = shell_dir / "region" / ANVIL_REGION_FILE_NAME
    shell_spike_manifest_path = shell_dir / "anvil-region-spike-manifest.json"
    shell_spike_readme_path = shell_dir / "README.txt"

    warnings = spike_result.warnings + (
        "This sampled save shell intentionally omits level.dat and other full-save metadata. Do not open it as a normal Minecraft world yet.",
        "Use MCA Selector for inspection, or copy only save-shell\\region\\r.0.0.mca into a backed-up test world's region folder.",
    )

    manifest = {
        "schema": ANVIL_SAVE_SHELL_SCHEMA,
        "version": ANVIL_SAVE_SHELL_VERSION,
        "project": {
            "name": config.name,
            "targetVersion": config.target_version,
            "worldWidth": config.width,
            "worldLength": config.length,
        },
        "donor": {
            "package": ANVIL_DONOR_PACKAGE,
            "license": ANVIL_DONOR_LICENSE,
            "url": ANVIL_DONOR_URL,
        },
        "artifacts": {
            "shellDir": shell_dir.name,
            "shellRegionFile": str(shell_region_path.relative_to(output_dir)),
            "shellReadme": str(shell_spike_readme_path.relative_to(output_dir)),
            "shellSpikeManifest": str(shell_spike_manifest_path.relative_to(output_dir)),
            "wrapperReadme": readme_path.name,
        },
        "sampleWindow": {
            "size": {"width": spike_result.sampled_width, "length": spike_result.sampled_length},
            "cropped": spike_result.cropped,
        },
        "shell": {
            "hasLevelDat": False,
            "safeForDirectMinecraftOpen": False,
            "suggestedInspectionFlow": "mca-selector-or-region-copy",
            "copyRegionIntoExistingWorld": {
                "relativeSourcePath": str(shell_region_path.relative_to(output_dir)),
                "targetSubfolder": "region",
                "backupRequired": True,
            },
        },
        "warnings": list(warnings),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme_path.write_text("\n".join(_build_readme_lines(config, spike_result)) + "\n", encoding="utf-8")

    return AnvilSaveShellResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        readme_path=readme_path,
        shell_dir=shell_dir,
        shell_region_path=shell_region_path,
        shell_spike_manifest_path=shell_spike_manifest_path,
        shell_spike_readme_path=shell_spike_readme_path,
        sampled_width=spike_result.sampled_width,
        sampled_length=spike_result.sampled_length,
        cropped=spike_result.cropped,
        warnings=warnings,
    )


def format_anvil_save_shell_result(result: AnvilSaveShellResult) -> str:
    lines = [
        f"Anvil save shell: {result.output_dir}",
        f"- shell dir: {result.shell_dir.name}",
        f"- region file: {result.shell_region_path.name}",
        f"- manifest: {result.manifest_path.name}",
        f"- readme: {result.readme_path.name}",
        f"- sampled window: {result.sampled_width} x {result.sampled_length}",
    ]
    for warning in result.warnings:
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)


def _build_readme_lines(config: ProjectConfig, spike_result: AnvilRegionSpikeResult) -> tuple[str, ...]:
    crop_line = (
        f"The logical world {config.width} x {config.length} was clipped to the first "
        f"{spike_result.sampled_width} x {spike_result.sampled_length} blocks."
        if spike_result.cropped
        else "The sampled window matches the logical world size."
    )
    return (
        "TitanForge sampled save-shell handoff",
        "",
        "What this is:",
        "- A save-like folder that carries one sampled r.0.0.mca under save-shell\\region\\.",
        "- A manual bridge from TitanForge planning artifacts toward real Minecraft save inspection.",
        "",
        "What this is not:",
        "- Not a full Minecraft save.",
        "- No level.dat is written yet, so Minecraft should not open this folder directly as a normal world.",
        "",
        "Use it like this:",
        "1. Inspect save-shell\\region\\r.0.0.mca in MCA Selector if you want to verify chunk contents safely.",
        "2. Or back up a throwaway test world and copy only save-shell\\region\\r.0.0.mca into that world's region\\ folder.",
        "3. Read save-shell\\anvil-region-spike-manifest.json for sampled block verification details.",
        "",
        "Sample window:",
        f"- {crop_line}",
        "",
        "Current limit:",
        "- This handoff exists to make the next manual export test obvious before TitanForge claims full save export support.",
    )
