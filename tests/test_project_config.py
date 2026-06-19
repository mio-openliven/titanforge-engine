from pathlib import Path
import tempfile
import unittest

from titanforge.core.project_review import write_project_review_page
from titanforge.core.project import load_project_config


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
