from pathlib import Path
import tempfile
import unittest

from titanforge.core.project_review import write_project_review_page
from titanforge.core.project import load_project_config
from titanforge.core.world_plan import build_world_plan, write_world_plan


class ProjectConfigTests(unittest.TestCase):
    def test_load_tiny_project_config(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        self.assertEqual(config.name, "Tiny Cinematic Valley")
        self.assertEqual(config.target_version, "1.21.11")
        self.assertEqual(config.width, 512)
        self.assertEqual(config.length, 512)
        self.assertIn("lost valley", config.premise)
        self.assertIn("slightly lost", config.player_experience)
        self.assertEqual(len(config.regions), 5)
        self.assertEqual(config.regions[0].title, "Harbor Town")
        self.assertEqual(config.regions[2].kind, "forest")
        self.assertEqual(
            config.pipeline,
            (
                "load_masks",
                "resolve_layout",
                "terrain_pass",
                "preview",
                "export",
            ),
        )

    def test_write_project_review_page(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "project-review.html"
            result = write_project_review_page(config, output_path)
            html = result.read_text(encoding="utf-8")

        self.assertEqual(result, output_path)
        self.assertIn("TitanForge World Brief", html)
        self.assertIn("Harbor Town", html)
        self.assertIn("64 .. 32000", html)
        self.assertIn("player moves from a safe farming edge", html)
        self.assertIn("project-draft", html)

    def test_build_world_plan_assigns_region_bounds(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        plan = build_world_plan(config)

        self.assertEqual(plan.width, 512)
        self.assertEqual(plan.length, 512)
        self.assertEqual(len(plan.regions), 5)
        self.assertEqual(plan.regions[0].title, "Harbor Town")
        self.assertEqual(plan.regions[0].x, 0)
        self.assertEqual(plan.regions[-1].x + plan.regions[-1].width, 512)
        self.assertTrue(all(region.length == 512 for region in plan.regions))
        self.assertTrue(all(region.anchors for region in plan.regions))
        for region in plan.regions:
            for anchor in region.anchors:
                self.assertGreaterEqual(anchor.x, region.x)
                self.assertLess(anchor.x, region.x + region.width)
                self.assertGreaterEqual(anchor.z, region.z)
                self.assertLess(anchor.z, region.z + region.length)

    def test_build_world_plan_assigns_story_specific_anchor_ids(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        plan = build_world_plan(config)

        anchors_by_title = {region.title: {anchor.id for anchor in region.anchors} for region in plan.regions}

        self.assertIn("arrival", anchors_by_title["Harbor Town"])
        self.assertIn("shoreline", anchors_by_title["Salt Coast"])
        self.assertIn("forest-core", anchors_by_title["Old Pine Forest"])
        self.assertIn("ridge-vista", anchors_by_title["Broken Ridge"])
        self.assertIn("center", anchors_by_title["River Village"])

    def test_write_world_plan_creates_json_output(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "world-plan.json"
            result = write_world_plan(config, output_path)
            data = output_path.read_text(encoding="utf-8")

        self.assertEqual(result, output_path)
        self.assertIn('"schema": "titanforge.world-plan"', data)
        self.assertIn('"title": "Harbor Town"', data)
        self.assertIn('"bounds"', data)
        self.assertIn('"anchors"', data)
        self.assertIn('"ridge-vista"', data)
