from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from titanforge.cli import main
from titanforge.masks.coastline import render_coastline_smoothing_preview
from titanforge.masks.png import read_png, write_rgba_png


WATER = (0, 102, 255, 255)
LAND = (59, 170, 53, 255)


class CoastlinePreviewTests(unittest.TestCase):
    def test_smoothing_softens_jagged_water_step(self) -> None:
        pixels = (
            (LAND, LAND, LAND, LAND),
            (LAND, WATER, WATER, LAND),
            (LAND, LAND, WATER, LAND),
            (LAND, LAND, LAND, LAND),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "coast.png"
            write_rgba_png(input_path, 4, 4, pixels)

            result = render_coastline_smoothing_preview(input_path, output_path)
            preview = read_png(output_path)

        self.assertGreaterEqual(result.changed_pixels, 1)
        self.assertEqual(preview.pixels[1][1], LAND)

    def test_smoothing_preserves_unknown_pixels(self) -> None:
        pixels = (
            ((1, 2, 3, 255), WATER),
            (LAND, LAND),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "coast.png"
            write_rgba_png(input_path, 2, 2, pixels)

            result = render_coastline_smoothing_preview(input_path, output_path)
            preview = read_png(output_path)

        self.assertEqual(result.unknown_pixels, 1)
        self.assertEqual(preview.pixels[0][0], (1, 2, 3, 255))

    def test_coastline_smoothing_cli_command(self) -> None:
        pixels = (
            (LAND, LAND, LAND, LAND),
            (LAND, WATER, WATER, LAND),
            (LAND, LAND, WATER, LAND),
            (LAND, LAND, LAND, LAND),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "coast.png"
            write_rgba_png(input_path, 4, 4, pixels)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["coastline-smoothing-preview", str(input_path), str(output_path)])

            preview = read_png(output_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Changed pixels:", stdout.getvalue())
        self.assertEqual(preview.pixels[1][1], LAND)
