from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from titanforge.cli import main
from titanforge.core.project import load_project_config
from titanforge.core.project_location import write_project_location


class ProjectLocationTests(unittest.TestCase):
    def test_write_project_location_creates_draft_and_location_outputs(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "project-location"
            result = write_project_location(config, output_dir, max_draft_side=256, use_cleanup_for_heightmap=True)
            manifest = json.loads((output_dir / "project-location-manifest.json").read_text(encoding="utf-8"))
            location_manifest = json.loads((output_dir / "location" / "manifest.json").read_text(encoding="utf-8"))
            draft_mask_exists = (output_dir / "draft" / "draft-mask.png").exists()
            location_review_exists = (output_dir / "location" / "review.html").exists()

        self.assertTrue(draft_mask_exists)
        self.assertTrue(location_review_exists)
        self.assertEqual(result.draft_result.blocks_per_pixel, 2)
        self.assertEqual(manifest["schema"], "titanforge.project-location")
        self.assertEqual(manifest["raster"]["blocksPerPixel"], 2)
        self.assertEqual(manifest["artifacts"]["draftDir"], "draft")
        self.assertEqual(manifest["artifacts"]["locationDir"], "location")
        self.assertEqual(manifest["artifacts"]["routePlan"], "draft\\route-plan.json")
        self.assertEqual(manifest["artifacts"]["routePreview"], "draft\\route-preview.png")
        self.assertEqual(manifest["artifacts"]["placementPlan"], "draft\\placement-plan.json")
        self.assertEqual(manifest["artifacts"]["placementPreview"], "draft\\placement-preview.png")
        self.assertEqual(manifest["artifacts"]["roadPlan"], "draft\\road-plan.json")
        self.assertEqual(manifest["artifacts"]["roadPreview"], "draft\\road-preview.png")
        self.assertEqual(manifest["artifacts"]["settlementPlan"], "draft\\settlement-plan.json")
        self.assertEqual(manifest["artifacts"]["settlementPreview"], "draft\\settlement-preview.png")
        self.assertEqual(len(manifest["warnings"]), 1)
        self.assertEqual(location_manifest["sourceMode"], "project-draft")
        self.assertEqual(location_manifest["terrain"]["cleanupApplied"], True)

    def test_project_location_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "project-location"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "project-location",
                        "examples/tiny_project/titanforge.toml",
                        str(output_dir),
                        "--max-draft-side",
                        "256",
                        "--use-cleanup-for-heightmap",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("Project location:", stdout.getvalue())
        self.assertIn("- draft dir: draft", stdout.getvalue())
        self.assertIn("- location dir: location", stdout.getvalue())
        self.assertIn("Blocks per pixel: 2", stdout.getvalue())
        self.assertIn("Warning:", stdout.getvalue())
