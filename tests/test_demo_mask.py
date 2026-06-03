import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from titanforge.cli import main
from titanforge.layouts.mask_layout import write_mask_layout
from titanforge.masks.analyzer import analyze_png_mask
from titanforge.masks.demo import generate_demo_mask
from titanforge.masks.png import read_png
from titanforge.preview.mask_preview import render_mask_preview
from titanforge.terrain.heightmap_preview import render_heightmap_preview


class DemoMaskTests(unittest.TestCase):
    def test_generate_demo_mask_contains_core_zones(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.png"

            result = generate_demo_mask(path, width=96, height=96)
            analysis = analyze_png_mask(path)

        zone_ids = {stat.zone.zone_id for stat in analysis.zone_stats}

        self.assertEqual(result.width, 96)
        self.assertEqual(result.height, 96)
        self.assertIn("water", zone_ids)
        self.assertIn("land", zone_ids)
        self.assertIn("beach", zone_ids)
        self.assertIn("road", zone_ids)
        self.assertIn("city", zone_ids)
        self.assertIn("forest", zone_ids)
        self.assertIn("mountain", zone_ids)
        self.assertIn("port", zone_ids)
        self.assertEqual(analysis.unknown_pixels, 0)

    def test_generate_demo_mask_rejects_tiny_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                generate_demo_mask(Path(directory) / "demo.png", width=16, height=16)

    def test_demo_mask_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.png"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["demo-mask", str(path), "--width", "64", "--height", "64"])

            image = read_png(path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Size: 64 x 64", stdout.getvalue())
        self.assertEqual(image.width, 64)
        self.assertEqual(image.height, 64)

    def test_demo_mask_runs_through_current_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "demo.png"
            preview_path = root / "preview.png"
            layout_path = root / "layout.json"
            heightmap_path = root / "heightmap.png"

            generate_demo_mask(mask_path, width=64, height=64)
            render_mask_preview(mask_path, preview_path)
            write_mask_layout(mask_path, layout_path)
            result = render_heightmap_preview(layout_path, heightmap_path)

        self.assertEqual(result.unknown_pixels, 0)
        self.assertEqual(result.width, 64)
        self.assertEqual(result.height, 64)
