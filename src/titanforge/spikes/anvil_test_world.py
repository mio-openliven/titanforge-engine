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
TEST_WORLD_MANIFEST = "anvil-test-world-manifest.json"
SESSION_LOCK_TEXT = "\u2603"
TEST_WORLD_NBT_ROOT_NAME = ""
VALID_VERIFICATION_STATUSES = ("pending", "in_progress", "failed", "passed")


class AnvilTestWorldVerificationError(RuntimeError):
    """Raised when a verification report update is invalid."""


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
    origin_x: int
    origin_z: int
    sampled_width: int
    sampled_length: int
    cropped: bool
    focus_region_title: str | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class AnvilTestWorldVerificationUpdateResult:
    report_path: Path
    manifest_path: Path | None
    status: str
    updated_check_id: str | None
    updated_check_status: str | None


@dataclass(frozen=True)
class AnvilTestWorldStatusResult:
    output_dir: Path
    manifest_path: Path
    report_path: Path
    checklist_path: Path
    readme_path: Path
    world_dir: Path
    level_dat_path: Path
    session_lock_path: Path
    region_path: Path
    verification_status: str
    verified_by_minecraft_open: bool
    checks: tuple[tuple[str, str], ...]
    origin_x: int
    origin_z: int
    sampled_width: int
    sampled_length: int
    cropped: bool
    focus_region_title: str | None
    current_sample_command: str
    next_sample_max_side: int | None
    next_sample_summary: str
    next_sample_command: str
    project_status_command: str
    warnings: tuple[str, ...]


def write_anvil_test_world(
    config: ProjectConfig,
    output_dir: Path,
    *,
    max_side: int = DEFAULT_SPIKE_MAX_SIDE,
    focus_region_title: str | None = None,
    anvil_module: Any | None = None,
    rerun_command_template: str | None = None,
    project_status_command: str | None = None,
) -> AnvilTestWorldResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    world_dir = output_dir / TEST_WORLD_DIR_NAME
    manifest_path = output_dir / TEST_WORLD_MANIFEST
    readme_path = output_dir / "README.txt"
    level_dat_path = world_dir / TEST_WORLD_LEVEL_DAT
    session_lock_path = world_dir / TEST_WORLD_SESSION_LOCK
    region_path = world_dir / "region" / ANVIL_REGION_FILE_NAME
    checklist_path = output_dir / TEST_WORLD_CHECKLIST
    report_path = output_dir / TEST_WORLD_REPORT

    spike_result = write_anvil_region_spike(
        config,
        world_dir,
        max_side=max_side,
        focus_region_title=focus_region_title,
        anvil_module=anvil_module,
    )
    world_name = _sanitize_world_name(config.name)
    level_dat_path.write_bytes(_build_level_dat_bytes(world_name))
    session_lock_path.write_bytes(SESSION_LOCK_TEXT.encode("utf-8"))

    warnings = spike_result.warnings + (
        "This is the first minimal test-world candidate, not a verified full Minecraft save.",
        "level.dat and session.lock are present, but this shell is still sampled and has not been validated by opening inside Minecraft in this automation pass.",
        "Use only for backed-up throwaway manual open tests.",
    )
    sample_growth = _build_sample_growth_guidance(
        world_width=config.width,
        world_length=config.length,
        sampled_width=spike_result.sampled_width,
        sampled_length=spike_result.sampled_length,
        rerun_command_template=rerun_command_template,
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
            "origin": {"x": spike_result.origin_x, "z": spike_result.origin_z},
            "size": {"width": spike_result.sampled_width, "length": spike_result.sampled_length},
            "cropped": spike_result.cropped,
            "focusRegion": spike_result.focus_region_title,
        },
        "sampleGrowth": sample_growth,
        "originHandoff": {
            "projectStatusCommand": project_status_command,
        },
        "worldShell": {
            "hasLevelDat": True,
            "hasSessionLock": True,
            "hasRegionFolder": True,
            "manualOpenCandidate": True,
            "verifiedByMinecraftOpen": False,
            "verificationStatus": "pending-manual-check",
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
        origin_x=spike_result.origin_x,
        origin_z=spike_result.origin_z,
        sampled_width=spike_result.sampled_width,
        sampled_length=spike_result.sampled_length,
        cropped=spike_result.cropped,
        focus_region_title=spike_result.focus_region_title,
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
        f"- sampled origin: x={result.origin_x} z={result.origin_z}",
        "Open next: verification-checklist.txt",
        "Record after manual test: verification-report.json",
        "Verification status: pending manual check",
    ]
    if result.focus_region_title:
        lines.append(f"- focus region: {result.focus_region_title}")
    for warning in result.warnings:
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)


def read_test_world_level_dat(data: bytes) -> tuple[str, dict[str, Any]]:
    return read_nbt(gzip.decompress(data))


def read_test_world_verification_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_test_world_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_test_world_status(output_dir: Path) -> AnvilTestWorldStatusResult:
    manifest_path = output_dir / TEST_WORLD_MANIFEST
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing test-world manifest: {manifest_path}")

    manifest = read_test_world_manifest(manifest_path)
    artifacts = manifest.get("artifacts", {})
    world_shell = manifest.get("worldShell", {})
    sample_window = manifest.get("sampleWindow", {})
    sample_growth = dict(manifest.get("sampleGrowth", {}))
    origin_handoff = dict(manifest.get("originHandoff", {}))
    origin = dict(sample_window.get("origin", {}))
    size = sample_window.get("size", {})

    report_path = output_dir / str(artifacts.get("verificationReport", TEST_WORLD_REPORT))
    if not report_path.exists():
        raise FileNotFoundError(f"Missing verification report: {report_path}")
    report = read_test_world_verification_report(report_path)
    verification_status = str(report.get("status", world_shell.get("verificationStatus", "pending")))
    checks = tuple(
        (str(check.get("id", "unknown")), str(check.get("status", "pending")))
        for check in report.get("checks", [])
    )

    checklist_path = output_dir / str(artifacts.get("verificationChecklist", TEST_WORLD_CHECKLIST))
    readme_path = output_dir / str(artifacts.get("wrapperReadme", "README.txt"))
    world_dir = output_dir / str(artifacts.get("worldDir", TEST_WORLD_DIR_NAME))
    level_dat_path = output_dir / str(artifacts.get("levelDat", Path(TEST_WORLD_DIR_NAME) / TEST_WORLD_LEVEL_DAT))
    session_lock_path = output_dir / str(artifacts.get("sessionLock", Path(TEST_WORLD_DIR_NAME) / TEST_WORLD_SESSION_LOCK))
    region_path = output_dir / str(artifacts.get("regionFile", Path(TEST_WORLD_DIR_NAME) / "region" / ANVIL_REGION_FILE_NAME))

    return AnvilTestWorldStatusResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        report_path=report_path,
        checklist_path=checklist_path,
        readme_path=readme_path,
        world_dir=world_dir,
        level_dat_path=level_dat_path,
        session_lock_path=session_lock_path,
        region_path=region_path,
        verification_status=verification_status,
        verified_by_minecraft_open=verification_status == "passed",
        checks=checks,
        origin_x=int(origin.get("x", 0)),
        origin_z=int(origin.get("z", 0)),
        sampled_width=int(size.get("width", 0)),
        sampled_length=int(size.get("length", 0)),
        cropped=bool(sample_window.get("cropped", False)),
        focus_region_title=(
            str(sample_window.get("focusRegion")) if sample_window.get("focusRegion") is not None else None
        ),
        current_sample_command=str(sample_growth.get("rerunCurrentCommand", "")),
        next_sample_max_side=(
            int(sample_growth["nextMaxSide"]) if sample_growth.get("nextMaxSide") is not None else None
        ),
        next_sample_summary=str(sample_growth.get("summary", "")),
        next_sample_command=str(sample_growth.get("nextSampleCommand", "")),
        project_status_command=str(origin_handoff.get("projectStatusCommand", "")),
        warnings=tuple(str(item) for item in manifest.get("warnings", [])),
    )


def update_test_world_verification_report(
    report_path: Path,
    *,
    status: str | None = None,
    check_id: str | None = None,
    check_status: str | None = None,
    check_note: str | None = None,
    report_note: str | None = None,
) -> AnvilTestWorldVerificationUpdateResult:
    if status is None and check_status is None and check_note is None and report_note is None:
        raise AnvilTestWorldVerificationError("No verification update was requested.")
    if check_status is not None and check_id is None:
        raise AnvilTestWorldVerificationError("--check-status requires --check.")
    if check_note is not None and check_id is None:
        raise AnvilTestWorldVerificationError("--check-note requires --check.")
    if status is not None and status not in VALID_VERIFICATION_STATUSES:
        raise AnvilTestWorldVerificationError(
            f"status must be one of {', '.join(VALID_VERIFICATION_STATUSES)}, got {status}."
        )
    if check_status is not None and check_status not in VALID_VERIFICATION_STATUSES:
        raise AnvilTestWorldVerificationError(
            f"check-status must be one of {', '.join(VALID_VERIFICATION_STATUSES)}, got {check_status}."
        )

    report = read_test_world_verification_report(report_path)

    target_check: dict[str, Any] | None = None
    if check_id is not None:
        for check in report.get("checks", []):
            if check.get("id") == check_id:
                target_check = check
                break
        if target_check is None:
            raise AnvilTestWorldVerificationError(f"Unknown check id: {check_id}.")

    check_status_changed = False
    if target_check is not None and check_status is not None:
        target_check["status"] = check_status
        check_status_changed = True
    if target_check is not None and check_note:
        existing = str(target_check.get("notes", ""))
        target_check["notes"] = _append_note(existing, check_note)

    if report_note:
        notes = list(report.get("notes", []))
        notes.append(report_note)
        report["notes"] = notes

    derived_status = _derive_verification_status(report)
    if check_status_changed:
        if status is not None and status != derived_status:
            raise AnvilTestWorldVerificationError(
                f"status {status} conflicts with derived verification status {derived_status}."
            )
        report["status"] = derived_status
    elif status is not None:
        if status == "passed" and _derive_verification_status(report) != "passed":
            raise AnvilTestWorldVerificationError(
                "status passed requires every verification check to be passed first."
            )
        report["status"] = status

    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_path = report_path.with_name(TEST_WORLD_MANIFEST)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        shell = dict(manifest.get("worldShell", {}))
        shell["verificationStatus"] = str(report.get("status", "pending"))
        shell["verifiedByMinecraftOpen"] = shell["verificationStatus"] == "passed"
        manifest["worldShell"] = shell
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        manifest_path = None

    return AnvilTestWorldVerificationUpdateResult(
        report_path=report_path,
        manifest_path=manifest_path,
        status=str(report.get("status", "pending")),
        updated_check_id=check_id,
        updated_check_status=check_status,
    )


def format_test_world_verification_update_result(result: AnvilTestWorldVerificationUpdateResult) -> str:
    lines = [
        f"Test-world verification report: {result.report_path}",
        f"- status: {result.status}",
    ]
    if result.updated_check_id is not None:
        lines.append(f"- updated check: {result.updated_check_id}")
    if result.updated_check_status is not None:
        lines.append(f"- check status: {result.updated_check_status}")
    if result.manifest_path is not None:
        lines.append(f"- manifest synced: {result.manifest_path.name}")
    return "\n".join(lines)


def format_test_world_status_result(result: AnvilTestWorldStatusResult) -> str:
    failed_checks = tuple(check_id for check_id, check_status in result.checks if check_status == "failed")
    lines = [
        f"Anvil test-world status: {result.output_dir}",
        f"- world dir: {result.world_dir.name}",
        f"- level.dat: {result.level_dat_path.name}",
        f"- session.lock: {result.session_lock_path.name}",
        f"- region file: {result.region_path.name}",
        f"- checklist: {result.checklist_path.name}",
        f"- report: {result.report_path.name}",
        f"- manifest: {result.manifest_path.name}",
        f"- readme: {result.readme_path.name}",
        f"- sampled window: {result.sampled_width} x {result.sampled_length}",
        f"- sampled origin: x={result.origin_x} z={result.origin_z}",
        f"- verification status: {result.verification_status}",
        f"- verified by Minecraft open: {'yes' if result.verified_by_minecraft_open else 'no'}",
    ]
    if result.focus_region_title:
        lines.append(f"- focus region: {result.focus_region_title}")
    if result.current_sample_command:
        lines.append(f"- rerun current sample: {result.current_sample_command}")
    if result.next_sample_summary:
        lines.append(f"- next sample: {result.next_sample_summary}")
    if result.next_sample_command:
        lines.append(f"- next sample command: {result.next_sample_command}")
    if result.verification_status == "failed":
        lines.append("- decision: stop sample growth and fix the current map direction first.")
        if result.project_status_command:
            lines.append(f"- go back to project handoff: {result.project_status_command}")
    elif result.verification_status == "passed":
        if result.next_sample_command:
            lines.append("- decision: current sample passed, so you can grow to the next sampled window.")
        elif result.project_status_command:
            lines.append("- decision: the safe sampled ladder is exhausted here; go back to the project handoff before trying a larger workflow.")
            lines.append(f"- go back to project handoff: {result.project_status_command}")
    elif result.verification_status == "in_progress":
        lines.append("- decision: finish the current manual checks before growing or editing the map.")
    else:
        lines.append("- decision: finish the current checklist before growing the sampled window.")
    if failed_checks:
        lines.append(f"- failed checks: {', '.join(failed_checks)}")
    if result.checks:
        lines.append("Checks:")
        for check_id, check_status in result.checks:
            lines.append(f"- {check_id}: {check_status}")
    if result.verification_status == "pending":
        lines.append("Open next: verification-checklist.txt")
        lines.append("Record after manual test: verification-report.json")
    else:
        lines.append("Open next: verification-report.json")
    for warning in result.warnings:
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)


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
        f"The logical world {config.width} x {config.length} was clipped to a sampled "
        f"{spike_result.sampled_width} x {spike_result.sampled_length} window."
        if spike_result.cropped
        else "The sampled window matches the logical world size."
    )
    focus_line = (
        f'- Focus region: "{spike_result.focus_region_title}"'
        if spike_result.focus_region_title
        else "- Focus region: world origin sample"
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
        "5. Open verification-checklist.txt first, then record the result in verification-report.json.",
        "",
        "Current honesty line:",
        "- This is the smallest test-world shell TitanForge can currently write without pretending that full save export is solved.",
        "- The world is still sampled, donor-backed, and unverified by an automated in-game open.",
        f"- Sample origin inside the logical world: x={spike_result.origin_x}, z={spike_result.origin_z}",
        focus_line,
        f"- {crop_line}",
    )


def _sanitize_world_name(name: str) -> str:
    compact = " ".join(part for part in name.split() if part)
    return compact[:64] if compact else "TitanForge Test World"


def _append_note(existing: str, new_note: str) -> str:
    return f"{existing}\n{new_note}".strip() if existing else new_note


def _derive_verification_status(report: dict[str, Any]) -> str:
    statuses = [str(check.get("status", "pending")) for check in report.get("checks", [])]
    if statuses and all(status == "passed" for status in statuses):
        return "passed"
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "in_progress" for status in statuses):
        return "in_progress"
    if any(status == "passed" for status in statuses):
        return "in_progress"
    return "pending"


def _build_checklist_lines(config: ProjectConfig, spike_result: Any) -> tuple[str, ...]:
    crop_line = (
        f"Sampled window only: {spike_result.sampled_width} x {spike_result.sampled_length} blocks from logical origin "
        f"x={spike_result.origin_x}, z={spike_result.origin_z} inside the "
        f"{config.width} x {config.length} world."
        if spike_result.cropped
        else "Sampled window matches the logical world size."
    )
    focus_line = (
        f'- Intended story focus: "{spike_result.focus_region_title}"'
        if spike_result.focus_region_title
        else "- Intended story focus: world origin sample"
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
        focus_line,
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
            "origin": {
                "x": spike_result.origin_x,
                "z": spike_result.origin_z,
            },
            "width": spike_result.sampled_width,
            "length": spike_result.sampled_length,
            "cropped": spike_result.cropped,
            "focusRegion": spike_result.focus_region_title,
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


def _build_sample_growth_guidance(
    *,
    world_width: int,
    world_length: int,
    sampled_width: int,
    sampled_length: int,
    rerun_command_template: str | None,
) -> dict[str, Any]:
    current_max_side = max(sampled_width, sampled_length)
    logical_limit = min(DEFAULT_SPIKE_MAX_SIDE, max(world_width, world_length))
    logical_limit -= logical_limit % 16
    if logical_limit <= 0:
        logical_limit = 16

    next_max_side = min(DEFAULT_SPIKE_MAX_SIDE, current_max_side * 2, logical_limit)
    next_max_side -= next_max_side % 16
    if next_max_side <= current_max_side:
        next_max_side = None

    rerun_current_command = (
        rerun_command_template.format(max_side=current_max_side)
        if rerun_command_template is not None
        else ""
    )
    next_sample_command = (
        rerun_command_template.format(max_side=next_max_side)
        if rerun_command_template is not None and next_max_side is not None
        else ""
    )

    if next_max_side is None:
        summary = "This sample already reaches the largest safe sampled test-world window TitanForge supports here."
    else:
        summary = (
            f"If the current manual-open test passes, grow next to {next_max_side} x {next_max_side} blocks."
        )

    return {
        "currentMaxSide": current_max_side,
        "nextMaxSide": next_max_side,
        "summary": summary,
        "rerunCurrentCommand": rerun_current_command,
        "nextSampleCommand": next_sample_command,
    }
