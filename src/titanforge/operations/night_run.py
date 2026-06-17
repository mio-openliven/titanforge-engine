from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from titanforge.locations.builder import build_location_pack


@dataclass(frozen=True)
class NightRunCase:
    index: int
    output_dir: str
    width: int
    height: int
    cleanup_applied: bool
    status: str
    errors: int
    warnings: int
    message: str


@dataclass(frozen=True)
class NightRunResult:
    output_dir: Path
    manifest_path: Path
    summary_path: Path
    requested_cases: int
    completed_cases: int
    succeeded_cases: int
    failed_cases: int
    elapsed_seconds: float


def run_night_run(
    output_dir: Path,
    *,
    count: int = 24,
    width: int = 128,
    height: int = 128,
    size_step: int = 32,
    max_minutes: float | None = None,
    use_cleanup_for_heightmap: bool = False,
    alternate_cleanup: bool = True,
) -> NightRunResult:
    if count < 1:
        raise ValueError("count must be at least 1.")
    if width < 1 or height < 1:
        raise ValueError("width and height must be positive.")
    if size_step < 0:
        raise ValueError("size_step must be zero or positive.")
    if max_minutes is not None and max_minutes <= 0:
        raise ValueError("max_minutes must be positive when provided.")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "night-run-manifest.json"
    summary_path = output_dir / "night-run-summary.txt"
    started_at = datetime.now(timezone.utc).isoformat()
    started_clock = time.monotonic()
    cases: list[NightRunCase] = []

    for index in range(1, count + 1):
        elapsed = time.monotonic() - started_clock
        if max_minutes is not None and elapsed >= max_minutes * 60:
            break

        case_width = width + ((index - 1) % 4) * size_step
        case_height = height + ((index - 1) % 4) * size_step
        cleanup_applied = use_cleanup_for_heightmap or (alternate_cleanup and index % 2 == 0)
        case_dir = output_dir / f"case-{index:04d}-{case_width}x{case_height}"

        try:
            result = build_location_pack(
                case_dir,
                demo=True,
                width=case_width,
                height=case_height,
                use_cleanup_for_heightmap=cleanup_applied,
            )
            status = "ok" if result.errors == 0 else "failed"
            message = "generated"
            errors = result.errors
            warnings = result.warnings
        except Exception as exc:  # noqa: BLE001 - batch runs must continue and report failures.
            status = "failed"
            message = f"{type(exc).__name__}: {exc}"
            errors = 1
            warnings = 0

        cases.append(
            NightRunCase(
                index=index,
                output_dir=case_dir.name,
                width=case_width,
                height=case_height,
                cleanup_applied=cleanup_applied,
                status=status,
                errors=errors,
                warnings=warnings,
                message=message,
            )
        )
        _write_night_run_outputs(output_dir, manifest_path, summary_path, started_at, cases, count, started_clock)

    return _build_result(output_dir, manifest_path, summary_path, count, cases, started_clock)


def format_night_run_result(result: NightRunResult) -> str:
    return "\n".join(
        [
            f"Night run: {result.output_dir}",
            f"- requested: {result.requested_cases}",
            f"- completed: {result.completed_cases}",
            f"- succeeded: {result.succeeded_cases}",
            f"- failed: {result.failed_cases}",
            f"- elapsed seconds: {result.elapsed_seconds:.2f}",
            f"- manifest: {result.manifest_path.name}",
            f"- summary: {result.summary_path.name}",
        ]
    )


def _build_result(
    output_dir: Path,
    manifest_path: Path,
    summary_path: Path,
    requested_cases: int,
    cases: list[NightRunCase],
    started_clock: float,
) -> NightRunResult:
    failed_cases = sum(1 for case in cases if case.status != "ok")
    completed_cases = len(cases)
    return NightRunResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        summary_path=summary_path,
        requested_cases=requested_cases,
        completed_cases=completed_cases,
        succeeded_cases=completed_cases - failed_cases,
        failed_cases=failed_cases,
        elapsed_seconds=time.monotonic() - started_clock,
    )


def _write_night_run_outputs(
    output_dir: Path,
    manifest_path: Path,
    summary_path: Path,
    started_at: str,
    cases: list[NightRunCase],
    requested_cases: int,
    started_clock: float,
) -> None:
    result = _build_result(output_dir, manifest_path, summary_path, requested_cases, cases, started_clock)
    manifest = {
        "schema": "titanforge.night-run",
        "version": 1,
        "startedAt": started_at,
        "outputDir": str(output_dir),
        "requestedCases": requested_cases,
        "completedCases": result.completed_cases,
        "succeededCases": result.succeeded_cases,
        "failedCases": result.failed_cases,
        "elapsedSeconds": round(result.elapsed_seconds, 3),
        "cases": [asdict(case) for case in cases],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(_format_summary(result, cases), encoding="utf-8")


def _format_summary(result: NightRunResult, cases: list[NightRunCase]) -> str:
    lines = [
        "TitanForge night run summary",
        "",
        f"Output: {result.output_dir}",
        f"Requested: {result.requested_cases}",
        f"Completed: {result.completed_cases}",
        f"Succeeded: {result.succeeded_cases}",
        f"Failed: {result.failed_cases}",
        f"Elapsed seconds: {result.elapsed_seconds:.2f}",
        "",
        "Cases:",
    ]
    for case in cases:
        lines.append(
            f"- {case.index:04d}: {case.status} {case.width}x{case.height} "
            f"cleanup={case.cleanup_applied} warnings={case.warnings} errors={case.errors} "
            f"dir={case.output_dir} message={case.message}"
        )
    lines.append("")
    return "\n".join(lines)
