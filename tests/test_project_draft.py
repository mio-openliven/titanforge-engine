from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from titanforge.cli import main
from titanforge.core.project import ProjectConfig, ProjectRegion, load_project_config
from titanforge.core.project_draft import write_project_draft
from titanforge.exporters.nbt_codec import read_nbt
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
            material_profile = json.loads((output_dir / "material-profile.json").read_text(encoding="utf-8"))
            export_request = json.loads((output_dir / "export-request.json").read_text(encoding="utf-8"))
            chunk_plan = json.loads((output_dir / "chunk-plan.json").read_text(encoding="utf-8"))
            block_fixture = json.loads((output_dir / "block-fixture.json").read_text(encoding="utf-8"))
            nbt_root_name, nbt_fixture = read_nbt((output_dir / "block-fixture.nbt").read_bytes())
            mcfunction_text = (output_dir / "place-fixture.mcfunction").read_text(encoding="utf-8")
            clear_mcfunction_text = (output_dir / "clear-fixture.mcfunction").read_text(encoding="utf-8")
            datapack_meta = json.loads((output_dir / "datapack-fixture" / "pack.mcmeta").read_text(encoding="utf-8"))
            with zipfile.ZipFile(output_dir / "datapack-fixture.zip") as archive:
                datapack_zip_entries = set(archive.namelist())
            transition_preview = read_png(output_dir / "transition-preview.png")
            route_preview = read_png(output_dir / "route-preview.png")
            placement_preview = read_png(output_dir / "placement-preview.png")
            road_preview = read_png(output_dir / "road-preview.png")
            settlement_preview = read_png(output_dir / "settlement-preview.png")
            analysis = analyze_png_mask(output_dir / "draft-mask.png")
            review_exists = (output_dir / "review.html").exists()
            plan_exists = (output_dir / "world-plan.json").exists()
            mask_exists = (output_dir / "draft-mask.png").exists()
            material_profile_exists = (output_dir / "material-profile.json").exists()
            export_request_exists = (output_dir / "export-request.json").exists()
            chunk_plan_exists = (output_dir / "chunk-plan.json").exists()
            block_fixture_exists = (output_dir / "block-fixture.json").exists()
            nbt_fixture_exists = (output_dir / "block-fixture.nbt").exists()
            mcfunction_fixture_exists = (output_dir / "place-fixture.mcfunction").exists()
            clear_mcfunction_fixture_exists = (output_dir / "clear-fixture.mcfunction").exists()
            datapack_fixture_exists = (output_dir / "datapack-fixture" / "pack.mcmeta").exists()
            datapack_zip_exists = (output_dir / "datapack-fixture.zip").exists()
            transition_plan_exists = (output_dir / "transition-plan.json").exists()
            transition_preview_exists = (output_dir / "transition-preview.png").exists()
            route_plan_exists = (output_dir / "route-plan.json").exists()
            route_preview_exists = (output_dir / "route-preview.png").exists()
            placement_plan_exists = (output_dir / "placement-plan.json").exists()
            placement_preview_exists = (output_dir / "placement-preview.png").exists()
            road_plan_exists = (output_dir / "road-plan.json").exists()
            road_preview_exists = (output_dir / "road-preview.png").exists()
            settlement_plan_exists = (output_dir / "settlement-plan.json").exists()
            settlement_preview_exists = (output_dir / "settlement-preview.png").exists()

        self.assertEqual(result.blocks_per_pixel, 2)
        self.assertTrue(review_exists)
        self.assertTrue(plan_exists)
        self.assertTrue(mask_exists)
        self.assertTrue(material_profile_exists)
        self.assertTrue(export_request_exists)
        self.assertTrue(chunk_plan_exists)
        self.assertTrue(block_fixture_exists)
        self.assertTrue(nbt_fixture_exists)
        self.assertTrue(mcfunction_fixture_exists)
        self.assertTrue(clear_mcfunction_fixture_exists)
        self.assertTrue(datapack_fixture_exists)
        self.assertTrue(datapack_zip_exists)
        self.assertTrue(transition_plan_exists)
        self.assertTrue(transition_preview_exists)
        self.assertTrue(route_plan_exists)
        self.assertTrue(route_preview_exists)
        self.assertTrue(placement_plan_exists)
        self.assertTrue(placement_preview_exists)
        self.assertTrue(road_plan_exists)
        self.assertTrue(road_preview_exists)
        self.assertTrue(settlement_plan_exists)
        self.assertTrue(settlement_preview_exists)
        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        self.assertEqual(transition_preview.width, 256)
        self.assertEqual(transition_preview.height, 256)
        self.assertEqual(route_preview.width, 256)
        self.assertEqual(route_preview.height, 256)
        self.assertEqual(placement_preview.width, 256)
        self.assertEqual(placement_preview.height, 256)
        self.assertEqual(road_preview.width, 256)
        self.assertEqual(road_preview.height, 256)
        self.assertEqual(settlement_preview.width, 256)
        self.assertEqual(settlement_preview.height, 256)
        self.assertEqual(manifest["schema"], "titanforge.project-draft")
        self.assertEqual(material_profile["adapter"]["targetVersion"], "1.21.11")
        self.assertEqual(material_profile["adapter"]["supported"], True)
        self.assertEqual(export_request["adapter"]["targetVersion"], "1.21.11")
        self.assertEqual(export_request["adapter"]["supported"], True)
        self.assertEqual(chunk_plan["adapter"]["targetVersion"], "1.21.11")
        self.assertEqual(chunk_plan["adapter"]["supported"], True)
        self.assertEqual(block_fixture["adapter"]["targetVersion"], "1.21.11")
        self.assertEqual(block_fixture["adapter"]["supported"], True)
        self.assertEqual(nbt_root_name, "TitanForgeFixture")
        self.assertEqual(nbt_fixture["targetVersion"], "1.21.11")
        self.assertEqual(nbt_fixture["supported"], True)
        self.assertIn("fill ", mcfunction_text)
        self.assertIn(" air", clear_mcfunction_text)
        self.assertEqual(datapack_meta["pack"]["min_format"], [94, 1])
        self.assertIn("pack.mcmeta", datapack_zip_entries)
        self.assertIn("data/titanforge/function/clear_fixture.mcfunction", datapack_zip_entries)
        self.assertEqual(manifest["raster"]["blocksPerPixel"], 2)
        self.assertEqual(manifest["world"]["width"], 512)
        self.assertEqual(len(manifest["warnings"]), 1)
        self.assertIn('"shape": "coast-band"', manifest_text)
        self.assertIn('"materialProfile": "material-profile.json"', manifest_text)
        self.assertIn('"exportRequest": "export-request.json"', manifest_text)
        self.assertIn('"chunkPlan": "chunk-plan.json"', manifest_text)
        self.assertIn('"blockFixture": "block-fixture.json"', manifest_text)
        self.assertIn('"nbtFixture": "block-fixture.nbt"', manifest_text)
        self.assertIn('"mcfunctionFixture": "place-fixture.mcfunction"', manifest_text)
        self.assertIn('"clearMcfunctionFixture": "clear-fixture.mcfunction"', manifest_text)
        self.assertIn('"datapackFixture": "datapack-fixture"', manifest_text)
        self.assertIn('"datapackFixtureZip": "datapack-fixture.zip"', manifest_text)
        self.assertIn('"transitionPlan": "transition-plan.json"', manifest_text)
        self.assertIn('"routePlan": "route-plan.json"', manifest_text)
        self.assertIn('"placementPlan": "placement-plan.json"', manifest_text)
        self.assertIn('"roadPlan": "road-plan.json"', manifest_text)
        self.assertIn('"settlementPlan": "settlement-plan.json"', manifest_text)
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
        self.assertTrue(any("Sparse world brief:" in warning for warning in result.warnings))

    def test_write_project_draft_warns_for_weak_zone_variety(self) -> None:
        config = ProjectConfig(
            name="Urban Stretch",
            target_version="1.21.11",
            width=1024,
            length=1024,
            premise="A long built-up corridor with too little contrast.",
            player_experience="The player should feel the need for stronger variety.",
            regions=(
                ProjectRegion(
                    title="South Gate",
                    kind="city",
                    story_role="arrival district",
                    mood="busy",
                    coverage_hint="25%",
                    notes="Main entry.",
                ),
                ProjectRegion(
                    title="Market Town",
                    kind="town",
                    story_role="trade zone",
                    mood="crowded",
                    coverage_hint="25%",
                    notes="Dense blocks.",
                ),
                ProjectRegion(
                    title="Old Village",
                    kind="village",
                    story_role="memory zone",
                    mood="quiet",
                    coverage_hint="25%",
                    notes="Still urban-family land use.",
                ),
                ProjectRegion(
                    title="Ruined Fort",
                    kind="fort",
                    story_role="late reveal",
                    mood="hard",
                    coverage_hint="25%",
                    notes="Still reads as one family in the draft.",
                ),
            ),
            pipeline=("preview",),
        )

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "draft"
            result = write_project_draft(config, output_dir, max_draft_side=1024)

        self.assertEqual(result.blocks_per_pixel, 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Weak zone variety:", result.warnings[0])

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
        self.assertIn("- material profile: material-profile.json", stdout.getvalue())
        self.assertIn("- export request: export-request.json", stdout.getvalue())
        self.assertIn("- chunk plan: chunk-plan.json", stdout.getvalue())
        self.assertIn("- block fixture: block-fixture.json", stdout.getvalue())
        self.assertIn("- NBT fixture: block-fixture.nbt", stdout.getvalue())
        self.assertIn("- mcfunction fixture: place-fixture.mcfunction", stdout.getvalue())
        self.assertIn("- clear mcfunction fixture: clear-fixture.mcfunction", stdout.getvalue())
        self.assertIn("- datapack fixture: datapack-fixture", stdout.getvalue())
        self.assertIn("- datapack zip: datapack-fixture.zip", stdout.getvalue())
        self.assertIn("- transition preview: transition-preview.png", stdout.getvalue())
        self.assertIn("- route preview: route-preview.png", stdout.getvalue())
        self.assertIn("- placement preview: placement-preview.png", stdout.getvalue())
        self.assertIn("- road preview: road-preview.png", stdout.getvalue())
        self.assertIn("- settlement preview: settlement-preview.png", stdout.getvalue())
