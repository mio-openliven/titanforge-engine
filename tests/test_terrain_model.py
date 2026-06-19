from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest

from titanforge.cli import main
from titanforge.layouts.mask_layout import write_mask_layout
from titanforge.masks.png import write_rgba_png
from titanforge.terrain.model import TERRAIN_GRID_SCHEMA, TERRAIN_GRID_VERSION, build_terrain_grid, write_terrain_grid


class TerrainGridTests(unittest.TestCase):
    def test_build_terrain_grid_uses_neutral_cells(self) -> None:
        water = (0, 102, 255, 255)
        city = (180, 74, 74, 255)
        unknown = (1, 2, 3, 255)
        pixels = (
            (water, city),
            (unknown, (0, 0, 0, 0)),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            write_rgba_png(mask_path, 2, 2, pixels)
            write_mask_layout(mask_path, layout_path)

            grid = build_terrain_grid(layout_path)

        self.assertEqual(grid.width, 2)
        self.assertEqual(grid.length, 2)
        self.assertEqual(len(grid.cells), 4)
        self.assertEqual(grid.unknown_cells, 1)
        self.assertEqual(grid.cells[0].zone_id, "water")
        self.assertEqual(grid.cells[0].surface, "water")
        self.assertFalse(grid.cells[0].buildable)
        self.assertEqual(grid.cells[1].zone_id, "city")
        self.assertEqual(grid.cells[1].surface, "urban")
        self.assertTrue(grid.cells[1].walkable)
        self.assertEqual(grid.cells[2].zone_id, "unknown")
        self.assertIsNone(grid.cells[2].elevation)
        self.assertEqual(grid.cells[3].zone_id, "void")

    def test_write_terrain_grid_creates_json_output(self) -> None:
        pixels = (((59, 170, 53, 255),),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            output_path = root / "terrain-grid.json"
            write_rgba_png(mask_path, 1, 1, pixels)
            write_mask_layout(mask_path, layout_path)

            result = write_terrain_grid(layout_path, output_path)
            grid = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result.width, 1)
        self.assertEqual(result.length, 1)
        self.assertEqual(result.cell_count, 1)
        self.assertEqual(result.unknown_cells, 0)
        self.assertEqual(grid["schema"], TERRAIN_GRID_SCHEMA)
        self.assertEqual(grid["version"], TERRAIN_GRID_VERSION)
        self.assertEqual(grid["cells"][0]["zone"], "land")
        self.assertEqual(grid["cells"][0]["surface"], "grassland")
        self.assertTrue(grid["cells"][0]["buildable"])

    def test_terrain_grid_cli_command_writes_output_file(self) -> None:
        pixels = (((119, 119, 119, 255),),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            output_path = root / "terrain-grid.json"
            write_rgba_png(mask_path, 1, 1, pixels)
            write_mask_layout(mask_path, layout_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["terrain-grid", str(layout_path), str(output_path)])

            grid = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertIn("Terrain grid:", stdout.getvalue())
        self.assertEqual(grid["cells"][0]["zone"], "mountain")
        self.assertFalse(grid["cells"][0]["walkable"])
