from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from titanforge.cli import main
from titanforge.masks.analyzer import analyze_png_mask
from titanforge.masks.png import PngError, read_png, write_rgba_png


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

    def test_analyze_mask_unknown_pixels_counts_beyond_display_cap(self) -> None:
        # Regression: unknown_pixels must not be capped at the top-20 display limit.
        # A mask with 25 distinct unknown colors must satisfy known + unknown == total.
        unknown_colors = tuple((i, i + 1, i + 2, 255) for i in range(1, 26))
        row = ((0, 102, 255, 255),) + unknown_colors  # 1 known water + 25 unknowns

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mask.png"
            write_rgba_png(path, 26, 1, (row,))
            analysis = analyze_png_mask(path)

        self.assertEqual(analysis.known_pixels + analysis.unknown_pixels, analysis.total_pixels)
        self.assertEqual(analysis.known_pixels, 1)
        self.assertEqual(analysis.unknown_pixels, 25)

    def test_mask_info_cli_reports_error_on_missing_file(self) -> None:
        # Regression: domain errors must surface as clean stderr messages, not tracebacks.
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = main(["mask-info", "/nonexistent/path/mask.png"])

        self.assertNotEqual(exit_code, 0)
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertIn("error:", stderr.getvalue())

    def test_read_png_rejects_bad_signature(self) -> None:
        # Regression: a file that is not a PNG must raise PngError, not AttributeError.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.png"
            path.write_bytes(b"\x00" * 64)
            with self.assertRaises(PngError):
                read_png(path)

    def test_read_png_rejects_corrupted_idat(self) -> None:
        # Regression: a PNG whose compressed stream is corrupt must raise PngError.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mask.png"
            write_rgba_png(path, 1, 1, (((0, 102, 255, 255),),))
            raw = bytearray(path.read_bytes())
            idat_offset = raw.index(b"IDAT")
            raw[idat_offset + 6] ^= 0xFF  # corrupt first byte of compressed payload
            path.write_bytes(bytes(raw))
            with self.assertRaises(PngError):
                read_png(path)
