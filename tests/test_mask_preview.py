import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from titanforge.cli import main
from titanforge.masks.png import read_png, write_rgba_png
from titanforge.preview.mask_preview import UNKNOWN_COLOR, render_mask_preview


class MaskPreviewTests(unittest.TestCase):
    def test_render_mask_preview_preserves_known_colors_and_marks_unknown(self) -> None:
        pixels = (
            ((0, 102, 255, 255), (59, 170, 53, 255)),
            ((12, 34, 56, 255), (0, 0, 0, 0)),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "preview.png"
            write_rgba_png(input_path, 2, 2, pixels)

            result = render_mask_preview(input_path, output_path)
            preview = read_png(output_path)

        self.assertEqual(result.known_pixels, 3)
        self.assertEqual(result.unknown_pixels, 1)
        self.assertEqual(preview.pixels[0][0], (0, 102, 255, 255))
        self.assertEqual(preview.pixels[0][1], (59, 170, 53, 255))
        self.assertEqual(preview.pixels[1][0], UNKNOWN_COLOR.rgba)
        self.assertEqual(preview.pixels[1][1], (0, 0, 0, 0))

    def test_mask_preview_cli_command_writes_output_file(self) -> None:
        pixels = (((0, 102, 255, 255), (9, 9, 9, 255)),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "mask.png"
            output_path = root / "preview.png"
            write_rgba_png(input_path, 2, 1, pixels)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["mask-preview", str(input_path), str(output_path)])

            preview = read_png(output_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Unknown pixels: 1", stdout.getvalue())
        self.assertEqual(preview.pixels[0][1], UNKNOWN_COLOR.rgba)
