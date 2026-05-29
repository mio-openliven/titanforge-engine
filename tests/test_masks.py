from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from titanforge.cli import main
from titanforge.masks.analyzer import analyze_png_mask
from titanforge.masks.png import read_png, write_rgba_png


class MaskPngTests(unittest.TestCase):
    def test_rgba_png_round_trip(self) -> None:
        pixels = (
            ((0, 102, 255, 255), (59, 170, 53, 255)),
            ((64, 64, 64, 255), (0, 0, 0, 0)),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mask.png"
            write_rgba_png(path, 2, 2, pixels)

            image = read_png(path)

        self.assertEqual(image.width, 2)
        self.assertEqual(image.height, 2)
        self.assertEqual(image.pixels, pixels)

    def test_analyze_mask_counts_known_and_unknown_colors(self) -> None:
        pixels = (
            ((0, 102, 255, 255), (0, 102, 255, 255), (59, 170, 53, 255)),
            ((64, 64, 64, 255), (1, 2, 3, 255), (0, 0, 0, 0)),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mask.png"
            write_rgba_png(path, 3, 2, pixels)

            analysis = analyze_png_mask(path)

        counts = {stat.zone.zone_id: stat.pixels for stat in analysis.zone_stats}
        unknown = {stat.color.rgba: stat.pixels for stat in analysis.unknown_color_stats}

        self.assertEqual(analysis.width, 3)
        self.assertEqual(analysis.height, 2)
        self.assertEqual(counts["water"], 2)
        self.assertEqual(counts["land"], 1)
        self.assertEqual(counts["road"], 1)
        self.assertEqual(counts["void"], 1)
        self.assertEqual(unknown[(1, 2, 3, 255)], 1)

    def test_mask_info_cli_command(self) -> None:
        pixels = (((0, 102, 255, 255),),)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mask.png"
            write_rgba_png(path, 1, 1, pixels)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["mask-info", str(path)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Known pixels: 1", stdout.getvalue())
