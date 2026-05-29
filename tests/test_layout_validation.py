from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from titanforge.cli import main
from titanforge.layouts.mask_layout import write_mask_layout
from titanforge.masks.png import write_rgba_png
from titanforge.validation.layout_report import validate_layout_file, write_layout_validation_report


class LayoutValidationTests(unittest.TestCase):
    def test_validate_layout_warns_about_unknown_colors(self) -> None:
        pixels = (((0, 102, 255, 255), (1, 2, 3, 255)),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            write_rgba_png(mask_path, 2, 1, pixels)
            write_mask_layout(mask_path, layout_path)

            result = validate_layout_file(layout_path)

        codes = {issue.code for issue in result.issues}
        self.assertFalse(result.has_errors)
        self.assertIn("mask.unknown-colors", codes)
        self.assertIn("zones.no-land", codes)

    def test_write_layout_validation_report(self) -> None:
        pixels = (((0, 102, 255, 255), (59, 170, 53, 255)),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            report_path = root / "report.txt"
            write_rgba_png(mask_path, 2, 1, pixels)
            write_mask_layout(mask_path, layout_path)

            result = write_layout_validation_report(layout_path, report_path)
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.error_count, 0)
        self.assertIn("TitanForge Layout Report", report)
        self.assertIn("Status: OK", report)

    def test_validate_layout_cli_command(self) -> None:
        pixels = (((59, 170, 53, 255),),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mask_path = root / "mask.png"
            layout_path = root / "layout.json"
            report_path = root / "report.txt"
            write_rgba_png(mask_path, 1, 1, pixels)
            write_mask_layout(mask_path, layout_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["validate-layout", str(layout_path), "--report", str(report_path)])

            self.assertTrue(report_path.exists())

        self.assertEqual(exit_code, 0)
        self.assertIn("Warnings:", stdout.getvalue())
