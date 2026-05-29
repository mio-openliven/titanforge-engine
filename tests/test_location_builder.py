from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest

from titanforge.cli import main
from titanforge.locations.builder import build_location_pack
from titanforge.masks.png import write_rgba_png


class LocationBuilderTests(unittest.TestCase):
    def test_build_demo_location_pack_creates_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "location"

            result = build_location_pack(output_dir, demo=True, width=64, height=64)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            for path in (
                result.mask_path,
                result.mask_preview_path,
                result.layout_path,
                result.heightmap_path,
                result.report_path,
                result.manifest_path,
            ):
                self.assertTrue(path.exists(), path)

        self.assertEqual(result.errors, 0)
        self.assertEqual(result.warnings, 0)
        self.assertEqual(manifest["schema"], "titanforge.location-pack")
        self.assertEqual(manifest["validation"], {"errors": 0, "warnings": 0})

    def test_build_location_pack_from_input_mask_reports_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_mask = root / "input.png"
            output_dir = root / "location"
            write_rgba_png(input_mask, 2, 1, (((0, 102, 255, 255), (1, 2, 3, 255)),))

            result = build_location_pack(output_dir, input_mask=input_mask)
            report = result.report_path.read_text(encoding="utf-8")

        self.assertEqual(result.errors, 0)
        self.assertGreater(result.warnings, 0)
        self.assertIn("mask.unknown-colors", report)

    def test_build_location_cli_command_defaults_to_demo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "location"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["build-location", str(output_dir), "--width", "64", "--height", "64"])

            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(manifest["sourceMode"], "demo")
        self.assertIn("Location pack:", stdout.getvalue())
