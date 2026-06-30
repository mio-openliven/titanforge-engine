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
from titanforge.spikes.anvil_save_shell import write_anvil_save_shell
from tests.test_anvil_region_spike import _FakeAnvilModule


class AnvilSaveShellTests(unittest.TestCase):
    def test_write_anvil_save_shell_creates_wrapper_and_shell(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "save-shell"
            result = write_anvil_save_shell(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            manifest = json.loads((output_dir / "anvil-save-shell-manifest.json").read_text(encoding="utf-8"))
            readme_text = (output_dir / "README.txt").read_text(encoding="utf-8")
            shell_region_exists = result.shell_region_path.exists()
            shell_spike_manifest_exists = result.shell_spike_manifest_path.exists()

        self.assertTrue(shell_region_exists)
        self.assertTrue(shell_spike_manifest_exists)
        self.assertEqual(manifest["schema"], "titanforge.spike.anvil-save-shell")
        self.assertEqual(manifest["artifacts"]["shellDir"], "save-shell")
        self.assertEqual(manifest["artifacts"]["shellRegionFile"], "save-shell\\region\\r.0.0.mca")
        self.assertEqual(manifest["shell"]["hasLevelDat"], False)
        self.assertEqual(manifest["shell"]["safeForDirectMinecraftOpen"], False)
        self.assertEqual(manifest["shell"]["copyRegionIntoExistingWorld"]["targetSubfolder"], "region")
        self.assertIn("MCA Selector", readme_text)
        self.assertIn("No level.dat is written yet", readme_text)
        self.assertTrue(any("omits level.dat" in warning for warning in result.warnings))

    def test_anvil_save_shell_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "save-shell"
            stdout = io.StringIO()

            with mock.patch("titanforge.spikes.anvil_region._load_anvil_module", return_value=_FakeAnvilModule):
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "anvil-save-shell",
                            str(Path("examples") / "tiny_project" / "titanforge.toml"),
                            str(output_dir),
                            "--max-side",
                            "128",
                        ]
                    )

            manifest_exists = (output_dir / "anvil-save-shell-manifest.json").exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(manifest_exists)
        self.assertIn("Anvil save shell:", stdout.getvalue())
        self.assertIn("- shell dir: save-shell", stdout.getvalue())

    def test_anvil_save_shell_cli_rejects_unaligned_sample_size(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "anvil-save-shell",
                    str(Path("examples") / "tiny_project" / "titanforge.toml"),
                    "out\\bad-save-shell",
                    "--max-side",
                    "130",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("--max-side must be divisible by 16", stderr.getvalue())
