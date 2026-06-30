from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from titanforge.cli import main
from titanforge.core.project import load_project_config
from titanforge.spikes.anvil_test_world import (
    format_test_world_status_result,
    read_test_world_level_dat,
    read_test_world_verification_report,
    summarize_test_world_status,
    update_test_world_verification_report,
    write_anvil_test_world,
)
from tests.test_anvil_region_spike import _FakeAnvilModule


class AnvilTestWorldTests(unittest.TestCase):
    def test_write_anvil_test_world_creates_minimal_shell(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "test-world"
            result = write_anvil_test_world(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            manifest = json.loads((output_dir / "anvil-test-world-manifest.json").read_text(encoding="utf-8"))
            readme_text = (output_dir / "README.txt").read_text(encoding="utf-8")
            checklist_text = (output_dir / "verification-checklist.txt").read_text(encoding="utf-8")
            verification_report = json.loads((output_dir / "verification-report.json").read_text(encoding="utf-8"))
            root_name, level_dat = read_test_world_level_dat((output_dir / "test-world" / "level.dat").read_bytes())
            session_lock_text = (output_dir / "test-world" / "session.lock").read_text(encoding="utf-8")
            region_exists = result.region_path.exists()

        self.assertTrue(region_exists)
        self.assertEqual(root_name, "")
        self.assertEqual(level_dat["Data"]["LevelName"], "Tiny Cinematic Valley")
        self.assertEqual(level_dat["Data"]["DataVersion"], 4671)
        self.assertEqual(level_dat["Data"]["Version"]["Id"], 4671)
        self.assertEqual(level_dat["Data"]["Difficulty"], True)
        self.assertEqual(session_lock_text, "\u2603")
        self.assertEqual(manifest["schema"], "titanforge.spike.anvil-test-world")
        self.assertEqual(manifest["artifacts"]["worldDir"], "test-world")
        self.assertEqual(manifest["artifacts"]["verificationChecklist"], "verification-checklist.txt")
        self.assertEqual(manifest["artifacts"]["verificationReport"], "verification-report.json")
        self.assertEqual(manifest["worldShell"]["manualOpenCandidate"], True)
        self.assertEqual(manifest["worldShell"]["verifiedByMinecraftOpen"], False)
        self.assertEqual(manifest["worldShell"]["verificationStatus"], "pending-manual-check")
        self.assertEqual(manifest["sampleGrowth"]["currentMaxSide"], 128)
        self.assertEqual(manifest["sampleGrowth"]["nextMaxSide"], 256)
        self.assertIn("grow next to 256 x 256", manifest["sampleGrowth"]["summary"])
        self.assertIn("smallest test-world shell", readme_text)
        self.assertIn("Open verification-checklist.txt first", readme_text)
        self.assertIn("Status: pending manual verification", checklist_text)
        self.assertIn("verification-report.json", checklist_text)
        self.assertEqual(verification_report["status"], "pending")
        self.assertEqual(verification_report["checks"][0]["id"], "mca-selector-open")
        self.assertEqual(verification_report["checks"][0]["status"], "pending")
        self.assertTrue(any("throwaway manual open tests" in warning for warning in result.warnings))

    def test_anvil_test_world_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "test-world"
            stdout = io.StringIO()

            with mock.patch("titanforge.spikes.anvil_region._load_anvil_module", return_value=_FakeAnvilModule):
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "anvil-test-world",
                            str(Path("examples") / "tiny_project" / "titanforge.toml"),
                            str(output_dir),
                            "--max-side",
                            "128",
                        ]
                    )

            manifest_exists = (output_dir / "anvil-test-world-manifest.json").exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(manifest_exists)
        self.assertIn("Anvil test world:", stdout.getvalue())
        self.assertIn("- level.dat: level.dat", stdout.getvalue())
        self.assertIn("- checklist: verification-checklist.txt", stdout.getvalue())
        self.assertIn("Open next: verification-checklist.txt", stdout.getvalue())
        self.assertIn("Record after manual test: verification-report.json", stdout.getvalue())
        self.assertIn("Verification status: pending manual check", stdout.getvalue())

    def test_anvil_test_world_cli_rejects_unaligned_sample_size(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "anvil-test-world",
                    str(Path("examples") / "tiny_project" / "titanforge.toml"),
                    "out\\bad-test-world",
                    "--max-side",
                    "130",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("--max-side must be divisible by 16", stderr.getvalue())

    def test_update_test_world_verification_report_updates_check_and_manifest(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "test-world"
            write_anvil_test_world(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            report_path = output_dir / "verification-report.json"
            result = update_test_world_verification_report(
                report_path,
                check_id="mca-selector-open",
                check_status="failed",
                check_note="Parser opened the file but chunks looked offset.",
                report_note="First manual review found a likely origin mismatch.",
            )
            report = read_test_world_verification_report(report_path)
            manifest = json.loads((output_dir / "anvil-test-world-manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.updated_check_id, "mca-selector-open")
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["checks"][0]["status"], "failed")
        self.assertIn("chunks looked offset", report["checks"][0]["notes"])
        self.assertIn("origin mismatch", report["notes"][-1])
        self.assertEqual(manifest["worldShell"]["verificationStatus"], "failed")
        self.assertEqual(manifest["worldShell"]["verifiedByMinecraftOpen"], False)

    def test_anvil_test_world_verify_cli_command(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "test-world"
            write_anvil_test_world(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "anvil-test-world-verify",
                        str(output_dir / "verification-report.json"),
                        "--check",
                        "minecraft-world-list",
                        "--check-status",
                        "in_progress",
                        "--check-note",
                        "World folder copied for a throwaway manual boot.",
                    ]
                )

            report = read_test_world_verification_report(output_dir / "verification-report.json")

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "in_progress")
        self.assertEqual(report["checks"][1]["status"], "in_progress")
        self.assertIn("throwaway manual boot", report["checks"][1]["notes"])
        self.assertIn("Test-world verification report:", stdout.getvalue())
        self.assertIn("- status: in_progress", stdout.getvalue())
        self.assertIn("- updated check: minecraft-world-list", stdout.getvalue())

    def test_anvil_test_world_verify_cli_rejects_conflicting_status(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "test-world"
            write_anvil_test_world(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "anvil-test-world-verify",
                        str(output_dir / "verification-report.json"),
                        "--status",
                        "passed",
                        "--check",
                        "mca-selector-open",
                        "--check-status",
                        "failed",
                    ]
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("conflicts with derived verification status failed", stderr.getvalue())

    def test_summarize_test_world_status_reads_current_report_state(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "test-world"
            write_anvil_test_world(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            update_test_world_verification_report(
                output_dir / "verification-report.json",
                check_id="mca-selector-open",
                check_status="failed",
                check_note="The sample opened but block placement looked shifted.",
            )
            result = summarize_test_world_status(output_dir)
            summary = format_test_world_status_result(result)

        self.assertEqual(result.verification_status, "failed")
        self.assertFalse(result.verified_by_minecraft_open)
        self.assertIn(("mca-selector-open", "failed"), result.checks)
        self.assertIn("- verification status: failed", summary)
        self.assertIn("- failed checks: mca-selector-open", summary)
        self.assertIn("- next sample:", summary)
        self.assertIn("Checks:", summary)
        self.assertIn("- mca-selector-open: failed", summary)
        self.assertIn("Open next: verification-report.json", summary)

    def test_anvil_test_world_status_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "test-world"
            with mock.patch("titanforge.spikes.anvil_region._load_anvil_module", return_value=_FakeAnvilModule):
                create_exit_code = main(
                    [
                        "anvil-test-world",
                        str(Path("examples") / "tiny_project" / "titanforge.toml"),
                        str(output_dir),
                        "--max-side",
                        "128",
                    ]
                )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["anvil-test-world-status", str(output_dir)])

        self.assertEqual(create_exit_code, 0)
        self.assertEqual(exit_code, 0)
        self.assertIn("Anvil test-world status:", stdout.getvalue())
        self.assertIn("- verification status: pending", stdout.getvalue())
        self.assertIn("- mca-selector-open: pending", stdout.getvalue())
        self.assertIn("- next sample:", stdout.getvalue())
        self.assertIn("- next sample command:", stdout.getvalue())
        self.assertIn("Open next: verification-checklist.txt", stdout.getvalue())
