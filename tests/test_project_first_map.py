from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from titanforge.cli import main
from titanforge.core.project import load_project_config
from titanforge.core.project_first_map import format_project_first_map_result, write_project_first_map


class ProjectFirstMapTests(unittest.TestCase):
    def test_write_project_first_map_creates_starter_project_and_location_pack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "first-world"
            result = write_project_first_map(
                project_dir,
                "First World",
                2048,
                1536,
                "coastal-valley",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            config = load_project_config(project_dir / "titanforge.toml")
            manifest = json.loads((project_dir / "first-map-manifest.json").read_text(encoding="utf-8"))
            bridge_manifest = json.loads((project_dir / "first-map" / "project-location-manifest.json").read_text(encoding="utf-8"))
            root_review_html = (project_dir / "review.html").read_text(encoding="utf-8")
            review_exists = (project_dir / "first-map" / "location" / "review.html").exists()
            summary = format_project_first_map_result(result)

        self.assertEqual(config.name, "First World")
        self.assertEqual(config.width, 2048)
        self.assertEqual(config.length, 1536)
        self.assertEqual(result.review_page_path, project_dir / "review.html")
        self.assertTrue(review_exists)
        self.assertEqual(manifest["schema"], "titanforge.first-map")
        self.assertEqual(manifest["project"]["preset"], "coastal-valley")
        self.assertEqual(manifest["project"]["configPath"], "titanforge.toml")
        self.assertEqual(manifest["artifacts"]["projectLocationDir"], "first-map")
        self.assertEqual(manifest["artifacts"]["rootReviewPage"], "review.html")
        self.assertEqual(manifest["artifacts"]["locationReviewPage"], "first-map\\location\\review.html")
        self.assertEqual(manifest["artifacts"]["bridgeManifest"], "first-map\\project-location-manifest.json")
        self.assertEqual(manifest["raster"]["blocksPerPixel"], 8)
        self.assertEqual(manifest["terrain"]["cleanupApplied"], True)
        self.assertEqual(bridge_manifest["schema"], "titanforge.project-location")
        self.assertIn("How Size Works", root_review_html)
        self.assertIn("Logical world size", root_review_html)
        self.assertIn("1 px = 8 blocks", root_review_html)
        self.assertIn("World scale", root_review_html)
        self.assertIn("Local district", root_review_html)
        self.assertIn("Change <code>width</code> or <code>length</code>", root_review_html)
        self.assertIn('href="first-map/location/review.html"', root_review_html)
        self.assertIn('href="first-map/draft/review.html"', root_review_html)
        self.assertIn('href="titanforge.toml"', root_review_html)
        self.assertIn('href="first-map/draft/datapack-fixture.zip"', root_review_html)
        self.assertIn("First map:", summary)
        self.assertIn("- root review: review.html", summary)
        self.assertIn("Logical world size: 2048 x 1536", summary)
        self.assertIn("World scale: Local district", summary)
        self.assertIn("Scale bridge: 1 px = 8 blocks", summary)
        self.assertIn("Open first: review.html", summary)

    def test_write_project_first_map_refuses_to_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "occupied"
            first_map_dir = project_dir / "first-map"
            first_map_dir.mkdir(parents=True, exist_ok=True)

            with self.assertRaises(FileExistsError):
                write_project_first_map(project_dir, "Occupied", 512, 512, "frontier-basin")

    def test_first_map_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "starter"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "first-map",
                        str(project_dir),
                        "--name",
                        "Starter Kingdom",
                        "--width",
                        "1024",
                        "--length",
                        "768",
                        "--preset",
                        "island-kingdom",
                        "--max-draft-side",
                        "256",
                    ]
                )

            manifest = json.loads((project_dir / "first-map-manifest.json").read_text(encoding="utf-8"))
            config = load_project_config(project_dir / "titanforge.toml")

        self.assertEqual(exit_code, 0)
        self.assertEqual(config.name, "Starter Kingdom")
        self.assertEqual(config.regions[0].title, "Crown Harbor")
        self.assertEqual(manifest["project"]["preset"], "island-kingdom")
        self.assertIn("First map:", stdout.getvalue())
        self.assertIn("- root review: review.html", stdout.getvalue())
        self.assertIn("World scale: Local district", stdout.getvalue())
        self.assertIn("Scale bridge: 1 px =", stdout.getvalue())
        self.assertIn("Open first: review.html", stdout.getvalue())
        self.assertIn("Validation: 0 errors, 0 warnings", stdout.getvalue())
