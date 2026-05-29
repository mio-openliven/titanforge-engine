from pathlib import Path
import tempfile
import unittest

from titanforge.inventory.scanner import format_size, scan_inventory


class InventoryTests(unittest.TestCase):
    def test_scan_inventory_counts_files_and_lfs_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mask.png").write_bytes(b"png")
            (root / "notes.txt").write_text("hello", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "ignored.pyc").write_bytes(b"cache")

            report = scan_inventory(root)

            self.assertEqual(len(report.files), 2)
            self.assertEqual(len(report.lfs_files), 1)
            self.assertEqual(report.extensions[".png"], 1)
            self.assertEqual(report.extensions[".txt"], 1)
            self.assertEqual(report.skipped_dirs, (Path("__pycache__"),))

    def test_format_size_uses_readable_units(self) -> None:
        self.assertEqual(format_size(512), "512.0 B")
        self.assertEqual(format_size(2048), "2.0 KB")

    def test_missing_inventory_path_raises_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            scan_inventory(Path("does-not-exist"))
