from __future__ import annotations

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from titanforge.cli import main
from titanforge.core.project import load_project_config
from titanforge.core.project_template import (
    ProjectTemplateError,
    build_project_template_config,
    format_project_template_result,
    write_project_template,
)


class ProjectTemplateTests(unittest.TestCase):
    def test_write_project_template_creates_starter_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "fog-coast"
            result = write_project_template(project_dir, "Fog Coast", 2048, 1536, "coastal-valley")
            config = load_project_config(result.config_path)
            summary = format_project_template_result(result)

        self.assertEqual(result.config_path, project_dir / "titanforge.toml")
        self.assertEqual(result.suggested_output_dir, project_dir / "first-map")
        self.assertEqual(config.name, "Fog Coast")
        self.assertEqual(config.target_version, "1.21.11")
        self.assertEqual(config.width, 2048)
        self.assertEqual(config.length, 1536)
        self.assertEqual(len(config.regions), 5)
        self.assertEqual(config.regions[0].title, "Harbor Town")
        self.assertEqual(config.regions[-1].kind, "mountains")
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
        self.assertIn("Project template:", summary)
        self.assertIn("Preset: coastal-valley", summary)
        self.assertIn("py -3.11 -m titanforge project-location", summary)
        self.assertIn("--use-cleanup-for-heightmap", summary)

    def test_build_project_template_config_rejects_invalid_size(self) -> None:
        with self.assertRaises(ProjectTemplateError):
            build_project_template_config("Too Small", 32, 512, "coastal-valley")

        with self.assertRaises(ProjectTemplateError):
            build_project_template_config("Too Large", 512, 64000, "coastal-valley")

    def test_write_project_template_refuses_to_overwrite_existing_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "existing"
            project_dir.mkdir(parents=True, exist_ok=True)
            (project_dir / "titanforge.toml").write_text("[project]\nname = \"Existing\"\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                write_project_template(project_dir, "Existing", 512, 512, "coastal-valley")

    def test_init_project_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "starter"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "init-project",
                        str(project_dir),
                        "--name",
                        "Starter Bay",
                        "--width",
                        "1024",
                        "--length",
                        "768",
                        "--preset",
                        "frontier-basin",
                    ]
                )

            config = load_project_config(project_dir / "titanforge.toml")

        self.assertEqual(exit_code, 0)
        self.assertEqual(config.name, "Starter Bay")
        self.assertEqual(config.width, 1024)
        self.assertEqual(config.length, 768)
        self.assertEqual(config.regions[0].title, "Gate Town")
        self.assertIn("Project template:", stdout.getvalue())
        self.assertIn("Preset: frontier-basin", stdout.getvalue())
        self.assertIn("first-map", stdout.getvalue())

    def test_init_project_cli_reports_invalid_size(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = main(["init-project", "out/world", "--width", "48", "--length", "512"])

        self.assertEqual(exit_code, 2)
        self.assertIn("width must stay between 64 and 32000 blocks", stderr.getvalue())
