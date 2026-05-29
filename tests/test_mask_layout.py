from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest

from titanforge.cli import main
from titanforge.layouts.mask_layout import LAYOUT_SCHEMA, LAYOUT_VERSION, build_mask_layout, write_mask_layout
from titanforge.masks.png import write_rgba_png


class MaskLayoutTests(unittest.TestCase):
    def test_build_mask_layout_contains_world_and_zone_data(self) -> None:
        pixels = (
            ((0, 102, 255, 255), (59, 170, 53, 255)),
            ((1, 2, 3, 255), (0, 0, 0, 0)),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mask.png"
            write_rgba_png(path, 2, 2, pixels)

            layout = build_mask_layout(path)

        self.assertEqual(layout["schema"], LAYOUT_SCHEMA)
        self.assertEqual(layout["version"], LAYOUT_VERSION)
        self.assertEqual(layout["world"], {"width": 2, "length": 2})
        self.assertEqual(layout["coverage"]["totalPixels"], 4)
        self.assertEqual(layout["coverage"]["knownPixels"], 3)
        self.assertEqual(layout["coverage"]["unknownPixels"], 1)

        zones = {zone["id"]: zone for zone in layout["zones"]}
        self.assertEqual(zones["water"]["pixels"], 1)
        self.assertEqual(zones["land"]["pixels"], 1)
        self.assertEqual(zones["void"]["pixels"], 1)
        self.assertEqual(layout["unknownColors"][0]["color"], "#010203")

    def test_write_mask_layout_creates_json_file(self) -> None:
        pixels = (((0, 102, 255, 255),),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "layout.json"
            write_rgba_png(input_path, 1, 1, pixels)

            result = write_mask_layout(input_path, output_path)
            layout = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result.width, 1)
        self.assertEqual(result.height, 1)
        self.assertEqual(result.zone_count, 1)
        self.assertEqual(result.unknown_color_count, 0)
        self.assertEqual(layout["zones"][0]["id"], "water")

    def test_mask_layout_cli_command_writes_output_file(self) -> None:
        pixels = (((59, 170, 53, 255),),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "layout.json"
            write_rgba_png(input_path, 1, 1, pixels)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["mask-layout", str(input_path), str(output_path)])

            layout = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertIn("Zones: 1", stdout.getvalue())
        self.assertEqual(layout["zones"][0]["id"], "land")
