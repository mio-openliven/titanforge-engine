import unittest
from pathlib import Path

from titanforge.core.project import load_project_config


class ProjectConfigTests(unittest.TestCase):
    def test_load_tiny_project_config(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))

        self.assertEqual(config.name, "Tiny Cinematic Valley")
        self.assertEqual(config.target_version, "1.21.11")
        self.assertEqual(config.width, 512)
        self.assertEqual(config.length, 512)
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
