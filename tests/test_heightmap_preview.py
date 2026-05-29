from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from titanforge.cli import main
from titanforge.layouts.mask_layout import write_mask_layout
from titanforge.masks.png import read_png, write_rgba_png
from titanforge.terrain.heightmap_preview import UNKNOWN_HEIGHT_COLOR, ZONE_HEIGHTS, render_heightmap_preview


class HeightmapPreviewTests(unittest.TestCase):
    def test_render_heightmap_preview_maps_zones_to_grayscale_heights(self) -> None:
        pixels = (
            ((0, 102, 255, 255), (59, 170, 53, 255), (119, 119, 119, 255)),
            ((1, 2, 3, 255), (0, 0, 0, 0), (194, 178, 128, 255)),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            output_path = root / "heightmap.png"
            write_rgba_png(mask_path, 3, 2, pixels)
            write_mask_layout(mask_path, layout_path)

            result = render_heightmap_preview(layout_path, output_path)
            heightmap = read_png(output_path)

        water = ZONE_HEIGHTS["water"]
        land = ZONE_HEIGHTS["land"]
        mountain = ZONE_HEIGHTS["mountain"]
        beach = ZONE_HEIGHTS["beach"]

        self.assertEqual(result.known_pixels, 5)
        self.assertEqual(result.unknown_pixels, 1)
        self.assertEqual(heightmap.pixels[0][0], (water, water, water, 255))
        self.assertEqual(heightmap.pixels[0][1], (land, land, land, 255))
        self.assertEqual(heightmap.pixels[0][2], (mountain, mountain, mountain, 255))
        self.assertEqual(heightmap.pixels[1][0], UNKNOWN_HEIGHT_COLOR)
        self.assertEqual(heightmap.pixels[1][1], (0, 0, 0, 0))
        self.assertEqual(heightmap.pixels[1][2], (beach, beach, beach, 255))

    def test_heightmap_preview_cli_command_writes_output_file(self) -> None:
        pixels = (((59, 170, 53, 255), (1, 2, 3, 255)),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            output_path = root / "heightmap.png"
            write_rgba_png(mask_path, 2, 1, pixels)
            write_mask_layout(mask_path, layout_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["heightmap-preview", str(layout_path), str(output_path)])

            heightmap = read_png(output_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Unknown pixels: 1", stdout.getvalue())
        self.assertEqual(heightmap.pixels[0][1], UNKNOWN_HEIGHT_COLOR)

    def test_render_heightmap_preview_can_use_mask_override(self) -> None:
        original_pixels = (((59, 170, 53, 255),),)
        override_pixels = (((0, 102, 255, 255),),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            override_path = root / "cleaned.png"
            layout_path = root / "layout.json"
            output_path = root / "heightmap.png"
            write_rgba_png(mask_path, 1, 1, original_pixels)
            write_rgba_png(override_path, 1, 1, override_pixels)
            write_mask_layout(mask_path, layout_path)

            result = render_heightmap_preview(layout_path, output_path, mask_override_path=override_path)
            heightmap = read_png(output_path)

        water = ZONE_HEIGHTS["water"]
        self.assertEqual(result.mask_path, override_path)
        self.assertEqual(heightmap.pixels[0][0], (water, water, water, 255))
