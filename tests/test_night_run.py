from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest

from titanforge.cli import main
from titanforge.operations.night_run import run_night_run


class NightRunTests(unittest.TestCase):
    def test_night_run_writes_progress_manifest_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "night"

            result = run_night_run(output_dir, count=3, width=32, height=32, size_step=8)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            summary = result.summary_path.read_text(encoding="utf-8")

        self.assertEqual(result.completed_cases, 3)
        self.assertEqual(result.failed_cases, 0)
        self.assertEqual(manifest["schema"], "titanforge.night-run")
        self.assertEqual(manifest["completedCases"], 3)
        self.assertEqual([case["width"] for case in manifest["cases"]], [32, 40, 48])
        self.assertIn("TitanForge night run summary", summary)

    def test_night_run_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "night"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["night-run", str(output_dir), "--count", "2", "--width", "32", "--height", "32"])
            manifest_exists = (output_dir / "night-run-manifest.json").exists()
            stdout_text = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertTrue(manifest_exists)
        self.assertIn("Night run:", stdout_text)
