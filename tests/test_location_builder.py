from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest

from titanforge.cli import main
from titanforge.locations.builder import build_location_pack
from titanforge.masks.png import read_png, write_rgba_png
from titanforge.terrain.heightmap_preview import ZONE_HEIGHTS


class LocationBuilderTests(unittest.TestCase):
    def test_build_demo_location_pack_creates_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "location"

            result = build_location_pack(output_dir, demo=True, width=64, height=64)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            for path in (
                result.mask_path,
                result.mask_preview_path,
                result.cleanup_preview_path,
                result.coastline_smoothing_preview_path,
                result.layout_path,
                result.terrain_color_preview_path,
                result.heightmap_path,
                result.report_path,
                result.review_page_path,
                result.manifest_path,
            ):
                self.assertTrue(path.exists(), path)

        self.assertEqual(result.errors, 0)
        self.assertEqual(result.warnings, 0)
        self.assertEqual(manifest["schema"], "titanforge.location-pack")
        self.assertEqual(manifest["validation"], {"errors": 0, "warnings": 0})
        self.assertEqual(manifest["artifacts"]["maskCleanupPreview"], "mask-cleanup-preview.png")
        self.assertEqual(manifest["artifacts"]["coastlineSmoothingPreview"], "coastline-smoothing-preview.png")
        self.assertEqual(manifest["artifacts"]["terrainColorPreview"], "terrain-color-preview.png")
        self.assertEqual(manifest["artifacts"]["reviewPage"], "review.html")
        self.assertEqual(manifest["terrain"], {"cleanupApplied": False, "heightmapSource": "mask.png"})

    def test_build_location_pack_writes_static_review_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "location"

            result = build_location_pack(output_dir, demo=True, width=64, height=64)
            review_html = result.review_page_path.read_text(encoding="utf-8")

        self.assertIn("<title>location - TitanForge Review</title>", review_html)
        self.assertIn('src="mask-preview.png"', review_html)
        self.assertIn('src="mask-cleanup-preview.png"', review_html)
        self.assertIn('src="coastline-smoothing-preview.png"', review_html)
        self.assertIn('src="terrain-color-preview.png"', review_html)
        self.assertIn('src="heightmap-preview.png"', review_html)
        self.assertIn("TitanForge Layout Report", review_html)
        self.assertIn("report.txt", review_html)

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
        self.assertIn("Review Notes:", report)
        self.assertIn("Some pixels use colors TitanForge does not recognize.", report)

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
        self.assertIn("- review page: review.html", stdout.getvalue())
        self.assertIn("- coastline smoothing preview: coastline-smoothing-preview.png", stdout.getvalue())
        self.assertIn("- terrain color preview: terrain-color-preview.png", stdout.getvalue())

    def test_build_location_can_use_cleanup_for_heightmap(self) -> None:
        water = (0, 102, 255, 255)
        land = (59, 170, 53, 255)
        pixels = (
            (water, water, water),
            (water, land, water),
            (water, water, water),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_mask = root / "input.png"
            output_dir = root / "location"
            write_rgba_png(input_mask, 3, 3, pixels)

            result = build_location_pack(output_dir, input_mask=input_mask, use_cleanup_for_heightmap=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            heightmap = read_png(result.heightmap_path)

        water_height = ZONE_HEIGHTS["water"]
        self.assertEqual(result.heightmap_source_path, result.cleanup_preview_path)
        self.assertEqual(manifest["terrain"], {"cleanupApplied": True, "heightmapSource": "mask-cleanup-preview.png"})
        self.assertEqual(heightmap.pixels[1][1], (water_height, water_height, water_height, 255))
