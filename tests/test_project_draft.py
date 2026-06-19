from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from titanforge.cli import main
from titanforge.core.project import ProjectConfig, ProjectRegion, load_project_config
from titanforge.core.project_draft import write_project_draft
from titanforge.masks.analyzer import analyze_png_mask
from titanforge.masks.png import read_png


class ProjectDraftTests(unittest.TestCase):
    def test_write_project_draft_creates_expected_artifacts(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "draft"
            result = write_project_draft(config, output_dir, max_draft_side=256)
            manifest_text = (output_dir / "draft-manifest.json").read_text(encoding="utf-8")
            manifest = json.loads(manifest_text)
            image = read_png(output_dir / "draft-mask.png")
            analysis = analyze_png_mask(output_dir / "draft-mask.png")
            review_exists = (output_dir / "review.html").exists()
            plan_exists = (output_dir / "world-plan.json").exists()
            mask_exists = (output_dir / "draft-mask.png").exists()

        self.assertEqual(result.blocks_per_pixel, 2)
        self.assertTrue(review_exists)
        self.assertTrue(plan_exists)
        self.assertTrue(mask_exists)
        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        self.assertEqual(manifest["schema"], "titanforge.project-draft")
        self.assertEqual(manifest["raster"]["blocksPerPixel"], 2)
        self.assertEqual(manifest["world"]["width"], 512)
        self.assertEqual(len(manifest["warnings"]), 1)
        self.assertIn('"shape": "coast-band"', manifest_text)
        zone_ids = {stat.zone.zone_id for stat in analysis.zone_stats}
        self.assertIn("city", zone_ids)
        self.assertIn("water", zone_ids)
        self.assertIn("forest", zone_ids)
        self.assertIn("mountain", zone_ids)
        self.assertEqual(analysis.unknown_pixels, 0)

    def test_project_draft_shapes_coast_and_mountain_directionally(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "draft"
            write_project_draft(config, output_dir, max_draft_side=256)
            manifest = json.loads((output_dir / "draft-manifest.json").read_text(encoding="utf-8"))
            image = read_png(output_dir / "draft-mask.png")

        coast_region = next(region for region in manifest["regions"] if region["zone"] == "water")
        mountain_region = next(region for region in manifest["regions"] if region["zone"] == "mountain")

        coast_x = coast_region["rasterBounds"]["x"] + coast_region["rasterBounds"]["width"] // 2
        mountain_x = mountain_region["rasterBounds"]["x"] + mountain_region["rasterBounds"]["width"] // 2

        self.assertNotEqual(image.pixels[0][coast_x], (0, 102, 255, 255))
        self.assertEqual(image.pixels[-1][coast_x], (0, 102, 255, 255))
        self.assertEqual(image.pixels[0][mountain_x], (119, 119, 119, 255))
        self.assertNotEqual(image.pixels[-1][mountain_x], (119, 119, 119, 255))

    def test_write_project_draft_scales_large_worlds(self) -> None:
        config = ProjectConfig(
            name="Mega Coast",
            target_version="1.21.11",
            width=32000,
            length=24000,
            premise="A very large coast world.",
            player_experience="The player should feel small.",
            regions=(
                ProjectRegion(
                    title="Open Sea",
                    kind="sea",
                    story_role="weather wall",
                    mood="cold",
                    coverage_hint="40%",
                    notes="Fog and long views.",
                ),
                ProjectRegion(
                    title="Green Mainland",
                    kind="forest",
                    story_role="exploration",
                    mood="dense",
                    coverage_hint="60%",
                    notes="Long walks inland.",
                ),
            ),
            pipeline=("preview",),
        )

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "draft"
            result = write_project_draft(config, output_dir, max_draft_side=1024)
            image = read_png(output_dir / "draft-mask.png")

        self.assertEqual(result.blocks_per_pixel, 32)
        self.assertEqual(result.raster_width, 1000)
        self.assertEqual(result.raster_length, 750)
        self.assertEqual(image.width, 1000)
        self.assertEqual(image.height, 750)
        self.assertGreaterEqual(len(result.warnings), 2)

    def test_project_draft_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "draft"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "project-draft",
                        "examples/tiny_project/titanforge.toml",
                        str(output_dir),
                        "--max-draft-side",
                        "256",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("Project draft:", stdout.getvalue())
        self.assertIn("Blocks per pixel: 2", stdout.getvalue())
        self.assertIn("Warning:", stdout.getvalue())
