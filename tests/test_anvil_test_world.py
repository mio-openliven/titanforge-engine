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
from titanforge.spikes.anvil_test_world import read_test_world_level_dat, write_anvil_test_world
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
        self.assertIn("smallest test-world shell", readme_text)
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
