from __future__ import annotations

from dataclasses import dataclass
import gzip
import json
from pathlib import Path
from typing import Any

from titanforge.core.project import ProjectConfig
from titanforge.exporters.minecraft_12111_structure_template import STRUCTURE_TEMPLATE_DATA_VERSION
from titanforge.exporters.nbt_codec import NbtByte, NbtLong, read_nbt, write_nbt
from titanforge.spikes.anvil_region import (
    ANVIL_DONOR_LICENSE,
    ANVIL_DONOR_PACKAGE,
    ANVIL_DONOR_URL,
    ANVIL_REGION_FILE_NAME,
    DEFAULT_SPIKE_MAX_SIDE,
    write_anvil_region_spike,
)


ANVIL_TEST_WORLD_SCHEMA = "titanforge.spike.anvil-test-world"
ANVIL_TEST_WORLD_VERSION = 1
TEST_WORLD_DIR_NAME = "test-world"
TEST_WORLD_LEVEL_DAT = "level.dat"
TEST_WORLD_SESSION_LOCK = "session.lock"
TEST_WORLD_CHECKLIST = "verification-checklist.txt"
TEST_WORLD_REPORT = "verification-report.json"
SESSION_LOCK_TEXT = "\u2603"
TEST_WORLD_NBT_ROOT_NAME = ""


@dataclass(frozen=True)
class AnvilTestWorldResult:
    output_dir: Path
    manifest_path: Path
    readme_path: Path
    world_dir: Path
    level_dat_path: Path
    session_lock_path: Path
    region_path: Path
    checklist_path: Path
    report_path: Path
    sampled_width: int
    sampled_length: int
    cropped: bool
    warnings: tuple[str, ...]


def write_anvil_test_world(
    config: ProjectConfig,
    output_dir: Path,
    *,
    max_side: int = DEFAULT_SPIKE_MAX_SIDE,
    anvil_module: Any | None = None,
) -> AnvilTestWorldResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    world_dir = output_dir / TEST_WORLD_DIR_NAME
    manifest_path = output_dir / "anvil-test-world-manifest.json"
    readme_path = output_dir / "README.txt"
    level_dat_path = world_dir / TEST_WORLD_LEVEL_DAT
    session_lock_path = world_dir / TEST_WORLD_SESSION_LOCK
    region_path = world_dir / "region" / ANVIL_REGION_FILE_NAME
    checklist_path = output_dir / TEST_WORLD_CHECKLIST
    report_path = output_dir / TEST_WORLD_REPORT

    spike_result = write_anvil_region_spike(config, world_dir, max_side=max_side, anvil_module=anvil_module)
    world_name = _sanitize_world_name(config.name)
    level_dat_path.write_bytes(_build_level_dat_bytes(world_name))
    session_lock_path.write_bytes(SESSION_LOCK_TEXT.encode("utf-8"))

    warnings = spike_result.warnings + (
        "This is the first minimal test-world candidate, not a verified full Minecraft save.",
        "level.dat and session.lock are present, but this shell is still sampled and has not been validated by opening inside Minecraft in this automation pass.",
        "Use only for backed-up throwaway manual open tests.",
    )

    manifest = {
        "schema": ANVIL_TEST_WORLD_SCHEMA,
        "version": ANVIL_TEST_WORLD_VERSION,
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
            "worldDir": world_dir.name,
            "levelDat": str(level_dat_path.relative_to(output_dir)),
            "sessionLock": str(session_lock_path.relative_to(output_dir)),
            "regionFile": str(region_path.relative_to(output_dir)),
            "regionSpikeManifest": str((world_dir / "anvil-region-spike-manifest.json").relative_to(output_dir)),
            "verificationChecklist": checklist_path.name,
            "verificationReport": report_path.name,
            "wrapperReadme": readme_path.name,
        },
        "sampleWindow": {
            "size": {"width": spike_result.sampled_width, "length": spike_result.sampled_length},
            "cropped": spike_result.cropped,
        },
        "worldShell": {
            "hasLevelDat": True,
            "hasSessionLock": True,
            "hasRegionFolder": True,
            "manualOpenCandidate": True,
            "verifiedByMinecraftOpen": False,
            "sampledExport": True,
            "throwawayOnly": True,
        },
        "warnings": list(warnings),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme_path.write_text("\n".join(_build_readme_lines(config, spike_result)) + "\n", encoding="utf-8")
    checklist_path.write_text("\n".join(_build_checklist_lines(config, spike_result)) + "\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(_build_verification_report(config, spike_result, checklist_path, report_path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return AnvilTestWorldResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        readme_path=readme_path,
        world_dir=world_dir,
        level_dat_path=level_dat_path,
        session_lock_path=session_lock_path,
        region_path=region_path,
        checklist_path=checklist_path,
        report_path=report_path,
        sampled_width=spike_result.sampled_width,
        sampled_length=spike_result.sampled_length,
        cropped=spike_result.cropped,
        warnings=warnings,
    )


def format_anvil_test_world_result(result: AnvilTestWorldResult) -> str:
    lines = [
        f"Anvil test world: {result.output_dir}",
        f"- world dir: {result.world_dir.name}",
        f"- level.dat: {result.level_dat_path.name}",
        f"- session.lock: {result.session_lock_path.name}",
        f"- region file: {result.region_path.name}",
        f"- checklist: {result.checklist_path.name}",
        f"- report: {result.report_path.name}",
        f"- manifest: {result.manifest_path.name}",
        f"- readme: {result.readme_path.name}",
        f"- sampled window: {result.sampled_width} x {result.sampled_length}",
    ]
    for warning in result.warnings:
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)


def read_test_world_level_dat(data: bytes) -> tuple[str, dict[str, Any]]:
    return read_nbt(gzip.decompress(data))


def _build_level_dat_bytes(world_name: str) -> bytes:
    payload = {
        "Data": {
            "DataVersion": STRUCTURE_TEMPLATE_DATA_VERSION,
            "Version": {
                "Id": STRUCTURE_TEMPLATE_DATA_VERSION,
                "Name": "1.21.11",
                "Series": "main",
                "Snapshot": False,
            },
            "LevelName": world_name,
            "GameType": 1,
            "SpawnX": 0,
            "SpawnY": 80,
            "SpawnZ": 0,
            "Time": NbtLong(0),
            "DayTime": NbtLong(6000),
            "LastPlayed": NbtLong(0),
            "allowCommands": True,
            "hardcore": False,
            "initialized": True,
            "MapFeatures": True,
            "DifficultyLocked": False,
            "Difficulty": NbtByte(1),
            "raining": False,
            "thundering": False,
            "clearWeatherTime": 0,
            "rainTime": 0,
            "thunderTime": 0,
            "version": 19133,
            "DataPacks": {
                "Enabled": ["vanilla"],
                "Disabled": [],
            },
        }
    }
    return gzip.compress(write_nbt(TEST_WORLD_NBT_ROOT_NAME, payload))


def _build_readme_lines(config: ProjectConfig, spike_result: Any) -> tuple[str, ...]:
    crop_line = (
        f"The logical world {config.width} x {config.length} was clipped to the first "
        f"{spike_result.sampled_width} x {spike_result.sampled_length} blocks."
        if spike_result.cropped
        else "The sampled window matches the logical world size."
    )
    return (
        "TitanForge minimal test-world candidate",
        "",
        "What this writes:",
        "- test-world\\level.dat",
        "- test-world\\session.lock",
        "- test-world\\region\\r.0.0.mca",
        "",
        "How to use it:",
        "1. Treat it as a throwaway manual open candidate only.",
        "2. Make sure Minecraft is closed before touching session.lock or copying this folder.",
        "3. If you test it in Minecraft, do so only after backing up the folder and only as a sampled experiment.",
        "4. Fill in verification-checklist.txt and verification-report.json after the manual test instead of trusting memory.",
        "",
        "Current honesty line:",
        "- This is the smallest test-world shell TitanForge can currently write without pretending that full save export is solved.",
        "- The world is still sampled, donor-backed, and unverified by an automated in-game open.",
        f"- {crop_line}",
    )


def _sanitize_world_name(name: str) -> str:
    compact = " ".join(part for part in name.split() if part)
    return compact[:64] if compact else "TitanForge Test World"


def _build_checklist_lines(config: ProjectConfig, spike_result: Any) -> tuple[str, ...]:
    crop_line = (
        f"Sampled window only: first {spike_result.sampled_width} x {spike_result.sampled_length} blocks from the logical "
        f"{config.width} x {config.length} world."
        if spike_result.cropped
        else "Sampled window matches the logical world size."
    )
    return (
        "TitanForge manual-open verification checklist",
        "",
        "Status: pending manual verification",
        "",
        "Safety first:",
        "- [ ] Minecraft was closed before touching the folder.",
        "- [ ] The test was done on a throwaway copy, not on a real working world.",
        "",
        "Open path A: MCA Selector",
        "- [ ] test-world\\region\\r.0.0.mca opened without a parse error.",
        "- [ ] The sampled chunks appeared at the expected origin area.",
        "- [ ] Obvious sampled blocks looked plausible instead of all-air corruption.",
        "",
        "Open path B: Minecraft manual test",
        "- [ ] The test-world folder appeared in the world list, or failed in a clearly recorded way.",
        "- [ ] If it opened, the spawn area did not hard-crash the client.",
        "- [ ] If it opened, the visible terrain/block sample matched the intended fixture direction at a rough level.",
        "",
        "After the test:",
        "- [ ] verification-report.json was updated with the outcome, date, and notes.",
        "",
        "Scope reminder:",
        f"- {crop_line}",
        "- This checklist does not mean verification already happened.",
    )


def _build_verification_report(
    config: ProjectConfig,
    spike_result: Any,
    checklist_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    return {
        "schema": "titanforge.spike.anvil-test-world-verification",
        "version": 1,
        "status": "pending",
        "project": {
            "name": config.name,
            "targetVersion": config.target_version,
        },
        "artifacts": {
            "checklist": checklist_path.name,
            "report": report_path.name,
            "worldDir": TEST_WORLD_DIR_NAME,
            "regionFile": str(Path(TEST_WORLD_DIR_NAME) / "region" / ANVIL_REGION_FILE_NAME),
        },
        "sampleWindow": {
            "width": spike_result.sampled_width,
            "length": spike_result.sampled_length,
            "cropped": spike_result.cropped,
        },
        "checks": [
            {
                "id": "mca-selector-open",
                "label": "MCA Selector opens sampled region",
                "status": "pending",
                "notes": "",
            },
            {
                "id": "minecraft-world-list",
                "label": "Minecraft recognizes the test-world candidate",
                "status": "pending",
                "notes": "",
            },
            {
                "id": "minecraft-open",
                "label": "Minecraft opens without immediate crash",
                "status": "pending",
                "notes": "",
            },
            {
                "id": "spawn-sanity",
                "label": "Spawn/sample looks plausibly aligned with the sampled export",
                "status": "pending",
                "notes": "",
            },
        ],
        "notes": [
            "Fill this report only after a manual test.",
            "Keep failed opens or corruption notes instead of deleting them.",
        ],
    }
