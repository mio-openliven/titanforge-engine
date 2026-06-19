from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from titanforge.cli import main
from titanforge.layouts.mask_layout import write_mask_layout
from titanforge.masks.png import read_png, write_rgba_png
from titanforge.terrain.color_preview import (
    UNKNOWN_TERRAIN_COLOR,
    ZONE_TERRAIN_COLORS,
    render_terrain_color_preview,
)


class TerrainColorPreviewTests(unittest.TestCase):
    def test_render_terrain_color_preview_maps_zones_to_colors(self) -> None:
        pixels = (
            (
                (0, 102, 255, 255),
                (194, 178, 128, 255),
                (214, 154, 45, 255),
                (64, 64, 64, 255),
            ),
            (
                (180, 74, 74, 255),
                (31, 122, 31, 255),
                (59, 170, 53, 255),
                (119, 119, 119, 255),
            ),
            (
                (0, 0, 0, 0),
                (1, 2, 3, 255),
                (59, 170, 53, 255),
                (0, 102, 255, 255),
            ),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            output_path = root / "terrain-color.png"
            write_rgba_png(mask_path, 4, 3, pixels)
            write_mask_layout(mask_path, layout_path)

            result = render_terrain_color_preview(layout_path, output_path)
            preview = read_png(output_path)

        self.assertEqual(result.known_pixels, 11)
        self.assertEqual(result.unknown_pixels, 1)
        self.assertEqual(preview.pixels[0][0], ZONE_TERRAIN_COLORS["water"])
        self.assertEqual(preview.pixels[0][1], ZONE_TERRAIN_COLORS["beach"])
        self.assertEqual(preview.pixels[0][2], ZONE_TERRAIN_COLORS["port"])
        self.assertEqual(preview.pixels[0][3], ZONE_TERRAIN_COLORS["road"])
        self.assertEqual(preview.pixels[1][0], ZONE_TERRAIN_COLORS["city"])
        self.assertEqual(preview.pixels[1][1], ZONE_TERRAIN_COLORS["forest"])
        self.assertEqual(preview.pixels[1][2], ZONE_TERRAIN_COLORS["land"])
        self.assertEqual(preview.pixels[1][3], ZONE_TERRAIN_COLORS["mountain"])
        self.assertEqual(preview.pixels[2][0], ZONE_TERRAIN_COLORS["void"])
        self.assertEqual(preview.pixels[2][1], UNKNOWN_TERRAIN_COLOR)

    def test_terrain_color_preview_cli_command_writes_output_file(self) -> None:
        pixels = (((59, 170, 53, 255), (1, 2, 3, 255)),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            output_path = root / "terrain-color.png"
            write_rgba_png(mask_path, 2, 1, pixels)
            write_mask_layout(mask_path, layout_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["terrain-color-preview", str(layout_path), str(output_path)])

            preview = read_png(output_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Unknown pixels: 1", stdout.getvalue())
        self.assertEqual(preview.pixels[0][0], ZONE_TERRAIN_COLORS["land"])
        self.assertEqual(preview.pixels[0][1], UNKNOWN_TERRAIN_COLOR)
