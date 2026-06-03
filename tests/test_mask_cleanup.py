from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from titanforge.cli import main
from titanforge.masks.cleanup import render_mask_cleanup_preview
from titanforge.masks.png import read_png, write_rgba_png


WATER = (0, 102, 255, 255)
LAND = (59, 170, 53, 255)


class MaskCleanupTests(unittest.TestCase):
    def test_cleanup_replaces_tiny_water_island_inside_land(self) -> None:
        pixels = (
            (LAND, LAND, LAND),
            (LAND, WATER, LAND),
            (LAND, LAND, LAND),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "cleanup.png"
            write_rgba_png(input_path, 3, 3, pixels)

            result = render_mask_cleanup_preview(input_path, output_path)
            cleanup = read_png(output_path)

        self.assertEqual(result.changed_pixels, 1)
        self.assertEqual(cleanup.pixels[1][1], LAND)

    def test_cleanup_replaces_tiny_land_island_inside_water(self) -> None:
        pixels = (
            (WATER, WATER, WATER),
            (WATER, LAND, WATER),
            (WATER, WATER, WATER),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "cleanup.png"
            write_rgba_png(input_path, 3, 3, pixels)

            result = render_mask_cleanup_preview(input_path, output_path)
            cleanup = read_png(output_path)

        self.assertEqual(result.changed_pixels, 1)
        self.assertEqual(cleanup.pixels[1][1], WATER)

    def test_cleanup_removes_water_noise_on_heterogeneous_land_border(self) -> None:
        # Regression: a stray WATER pixel surrounded by a mix of land-family zones
        # (beach/road/forest) must be replaced.
        # Old code: thresholded per zone_id; no single zone reached threshold=5.
        # New code: thresholds on family total (8 opposing neighbors >= 5).
        BEACH = (194, 178, 128, 255)
        ROAD = (64, 64, 64, 255)
        FOREST = (31, 122, 31, 255)
        pixels = (
            (BEACH, ROAD, FOREST),
            (ROAD, WATER, BEACH),
            (FOREST, BEACH, ROAD),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "cleanup.png"
            write_rgba_png(input_path, 3, 3, pixels)

            result = render_mask_cleanup_preview(input_path, output_path, threshold=5)
            cleanup = read_png(output_path)

        self.assertEqual(result.changed_pixels, 1)
        self.assertNotEqual(cleanup.pixels[1][1], WATER)

    def test_mask_cleanup_cli_command(self) -> None:
        pixels = (
            (WATER, WATER, WATER),
            (WATER, LAND, WATER),
            (WATER, WATER, WATER),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "cleanup.png"
            write_rgba_png(input_path, 3, 3, pixels)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["mask-cleanup-preview", str(input_path), str(output_path)])

            cleanup = read_png(output_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Changed pixels: 1", stdout.getvalue())
        self.assertEqual(cleanup.pixels[1][1], WATER)
