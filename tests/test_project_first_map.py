from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from titanforge.cli import main
from titanforge.core.project import load_project_config
from titanforge.core.project_first_map import (
    build_first_map_test_world_strategy,
    format_project_first_map_result,
    format_project_first_map_status_result,
    suggest_first_map_test_world_max_side,
    summarize_project_first_map_status,
    write_project_first_map_test_world,
    write_project_first_map,
)
from titanforge.spikes.anvil_test_world import update_test_world_verification_report
from tests.test_anvil_region_spike import _FakeAnvilModule


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
        self.assertEqual(manifest["guidance"]["worldScale"]["label"], "Local district")
        self.assertIn("Good for one town plus nearby coast", manifest["guidance"]["worldScale"]["summary"])
        self.assertIn("comfortable for local travel beats", manifest["guidance"]["worldScale"]["planningNote"])
        self.assertIn("A cinematic coast-to-mountain story space", manifest["guidance"]["preset"]["story"])
        self.assertIn("The player should feel grounded at first", manifest["guidance"]["preset"]["playerFeeling"])
        self.assertEqual(
            manifest["guidance"]["preset"]["keyRegions"][:3],
            ["Harbor Town", "Salt Coast", "Old Pine Forest"],
        )
        self.assertEqual(
            manifest["guidance"]["worldSizeEdits"]["editFile"],
            "titanforge.toml",
        )
        self.assertEqual(
            manifest["guidance"]["worldSizeEdits"]["allowedRange"]["minBlocks"],
            64,
        )
        self.assertEqual(
            manifest["guidance"]["worldSizeEdits"]["allowedRange"]["maxBlocks"],
            32000,
        )
        self.assertEqual(
            manifest["guidance"]["worldSizeEdits"]["examples"][0]["label"],
            "Smaller test map",
        )
        self.assertEqual(
            manifest["guidance"]["worldSizeEdits"]["examples"][0]["width"],
            256,
        )
        self.assertEqual(
            manifest["guidance"]["worldSizeEdits"]["examples"][0]["length"],
            192,
        )
        self.assertEqual(
            manifest["guidance"]["worldSizeEdits"]["examples"][1]["scaleLabel"],
            "Local district",
        )
        self.assertIn(
            '--width 8192 --length 6144',
            manifest["guidance"]["worldSizeEdits"]["examples"][2]["rerunCommand"],
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["routePreview"],
            "first-map\\draft\\route-preview.png",
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["routePlan"],
            "first-map\\draft\\route-plan.json",
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["recommendedWalkthrough"][0]["stepId"],
            "step-01",
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["recommendedWalkthrough"][0]["title"],
            "Start here",
        )
        self.assertIn(
            "Open the first story entry point in Harbor Town.",
            manifest["guidance"]["storyRoutes"]["recommendedWalkthrough"][0]["summary"],
        )
        self.assertIn(
            '--focus-anchor "arrival"',
            manifest["guidance"]["storyRoutes"]["recommendedWalkthrough"][0]["command"],
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["recommendedWalkthrough"][0]["outputDir"],
            "minecraft-test-world-harbor-town-arrival",
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["recommendedWalkthrough"][-1]["title"],
            "Final reveal",
        )
        self.assertIn(
            "Broken Ridge",
            manifest["guidance"]["storyRoutes"]["recommendedWalkthrough"][-1]["summary"],
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["routeSamples"][0]["routeId"],
            "region-00",
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["routeSamples"][0]["kind"],
            "intra-region",
        )
        self.assertIn(
            "Harbor Town / arrival -> Harbor Town / center",
            manifest["guidance"]["storyRoutes"]["routeSamples"][0]["summary"],
        )
        self.assertIn(
            '--focus-anchor "arrival"',
            manifest["guidance"]["storyRoutes"]["routeSamples"][0]["startCommand"],
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["routeSamples"][0]["startOutputDir"],
            "minecraft-test-world-harbor-town-arrival",
        )
        self.assertIn(
            '--focus-anchor "center"',
            manifest["guidance"]["storyRoutes"]["routeSamples"][0]["endCommand"],
        )
        self.assertEqual(
            manifest["guidance"]["storyRoutes"]["routeSamples"][0]["endOutputDir"],
            "minecraft-test-world-harbor-town-center",
        )
        self.assertEqual(manifest["guidance"]["actionPlan"]["openSequence"][0]["id"], "root-review")
        self.assertEqual(manifest["guidance"]["actionPlan"]["openSequence"][0]["path"], "review.html")
        self.assertEqual(
            manifest["guidance"]["actionPlan"]["openSequence"][1]["path"],
            "first-map\\location\\review.html",
        )
        self.assertIn(
            "project-location",
            manifest["guidance"]["actionPlan"]["nextActions"][0]["commandHint"],
        )
        self.assertEqual(
            manifest["guidance"]["actionPlan"]["nextActions"][1]["path"],
            "first-map\\draft\\fixture-summary.json",
        )
        self.assertEqual(manifest["commands"]["presetCatalog"], "py -3.11 -m titanforge preset-catalog")
        self.assertEqual(manifest["commands"]["presetCatalogJson"], "py -3.11 -m titanforge preset-catalog --json")
        self.assertIn("py -3.11 -m titanforge first-map", manifest["commands"]["rerunFirstMap"])
        self.assertIn("--preset coastal-valley", manifest["commands"]["rerunFirstMap"])
        self.assertIn("py -3.11 -m titanforge project-location", manifest["commands"]["rerunProjectLocation"])
        self.assertEqual(manifest["commands"]["buildTestWorld"], 'py -3.11 -m titanforge first-map-test-world "first-world" --max-side 128')
        self.assertEqual(manifest["commands"]["testWorldStatus"], 'py -3.11 -m titanforge anvil-test-world-status "minecraft-test-world"')
        self.assertEqual(
            manifest["minecraftHandoff"]["artifacts"]["fixtureSummary"],
            "first-map\\draft\\fixture-summary.json",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["requiresOptionalExtra"],
            "py -3.11 -m pip install -e .[donor-spikes]",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["buildCommand"],
            'py -3.11 -m titanforge first-map-test-world "first-world" --max-side 128',
        )
        self.assertIn(
            "disposable centered sample",
            manifest["minecraftHandoff"]["testWorld"]["recommendedStart"]["summary"],
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["recommendedStart"]["installExtraCommand"],
            "py -3.11 -m pip install -e .[donor-spikes]",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["recommendedStart"]["buildCommand"],
            'py -3.11 -m titanforge first-map-test-world "first-world" --max-side 128',
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["recommendedStart"]["outputDir"],
            "minecraft-test-world",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["recommendedStart"]["checklistPath"],
            "minecraft-test-world\\verification-checklist.txt",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["focusRegionCommands"][0]["regionTitle"],
            "Harbor Town",
        )
        self.assertIn(
            '--focus-region "Harbor Town"',
            manifest["minecraftHandoff"]["testWorld"]["focusRegionCommands"][0]["command"],
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["focusRegionCommands"][0]["outputDir"],
            "minecraft-test-world-harbor-town",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["focusAnchorCommands"][0]["anchorLabel"],
            "Harbor Town / arrival",
        )
        self.assertIn(
            '--focus-anchor "arrival"',
            manifest["minecraftHandoff"]["testWorld"]["focusAnchorCommands"][0]["command"],
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["focusAnchorCommands"][0]["outputDir"],
            "minecraft-test-world-harbor-town-arrival",
        )
        self.assertEqual(manifest["minecraftHandoff"]["testWorld"]["outputDir"], "minecraft-test-world")
        self.assertEqual(manifest["minecraftHandoff"]["testWorld"]["strategy"]["recommendedMaxSide"], 128)
        self.assertEqual(manifest["minecraftHandoff"]["testWorld"]["strategy"]["recommendedRegionFileCount"], 1)
        self.assertEqual(
            manifest["minecraftHandoff"]["testWorld"]["strategy"]["regionFileSummary"],
            "The starter sample should write 1 sampled .mca file under test-world\\region\\.",
        )
        self.assertEqual(manifest["minecraftHandoff"]["testWorld"]["strategy"]["firstMultiRegionMaxSide"], 1024)
        self.assertEqual(manifest["minecraftHandoff"]["testWorld"]["strategy"]["firstMultiRegionRegionFileCount"], 4)
        self.assertIn(
            "--max-side 1024",
            manifest["minecraftHandoff"]["testWorld"]["strategy"]["multiRegionSummary"],
        )
        self.assertIn(
            "4 sampled .mca files",
            manifest["minecraftHandoff"]["testWorld"]["strategy"]["multiRegionSummary"],
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["reviewOrder"][0]["id"],
            "fixture-summary",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["reviewOrder"][1]["path"],
            "first-map\\draft\\fixture-commands.txt",
        )
        self.assertEqual(
            manifest["minecraftHandoff"]["reviewOrder"][2]["path"],
            "first-map\\draft\\datapack-fixture.zip",
        )
        self.assertEqual(manifest["artifacts"]["projectLocationDir"], "first-map")
        self.assertEqual(manifest["artifacts"]["rootReviewPage"], "review.html")
        self.assertEqual(manifest["artifacts"]["locationReviewPage"], "first-map\\location\\review.html")
        self.assertEqual(manifest["artifacts"]["bridgeManifest"], "first-map\\project-location-manifest.json")
        self.assertEqual(manifest["artifacts"]["routePlan"], "first-map\\draft\\route-plan.json")
        self.assertEqual(manifest["artifacts"]["routePreview"], "first-map\\draft\\route-preview.png")
        self.assertEqual(manifest["raster"]["blocksPerPixel"], 8)
        self.assertEqual(manifest["terrain"]["cleanupApplied"], True)
        self.assertEqual(bridge_manifest["schema"], "titanforge.project-location")
        self.assertIn("How Size Works", root_review_html)
        self.assertIn("Preset Intent", root_review_html)
        self.assertIn("Story Routes", root_review_html)
        self.assertIn("Preset story", root_review_html)
        self.assertIn("Harbor Town, Salt Coast, Old Pine Forest, +2 more", root_review_html)
        self.assertIn("Logical world size", root_review_html)
        self.assertIn("1 px = 8 blocks", root_review_html)
        self.assertIn("World scale", root_review_html)
        self.assertIn("Change size safely", root_review_html)
        self.assertIn("64 .. 32000", root_review_html)
        self.assertIn("Smaller test map", root_review_html)
        self.assertIn("--width 16000 --length 12000", root_review_html)
        self.assertIn("Local district", root_review_html)
        self.assertIn("Change <code>width</code> or <code>length</code>", root_review_html)
        self.assertIn('href="first-map/location/review.html"', root_review_html)
        self.assertIn('href="first-map/draft/review.html"', root_review_html)
        self.assertIn('href="first-map/draft/route-preview.png"', root_review_html)
        self.assertIn('href="first-map/draft/route-plan.json"', root_review_html)
        self.assertIn('href="titanforge.toml"', root_review_html)
        self.assertIn('href="first-map/draft/datapack-fixture.zip"', root_review_html)
        self.assertIn("Recommended walkthrough", root_review_html)
        self.assertIn("Full route sample pairs", root_review_html)
        self.assertIn("step-01: Start here", root_review_html)
        self.assertIn("region-00", root_review_html)
        self.assertIn("minecraft-test-world-harbor-town-center", root_review_html)
        self.assertIn("Recommended first manual-open path", root_review_html)
        self.assertIn("Why this sample size", root_review_html)
        self.assertIn("Sample file scope", root_review_html)
        self.assertIn("1 sampled .mca file under test-world\\region\\", root_review_html)
        self.assertIn("--max-side 1024", root_review_html)
        self.assertIn("4 sampled .mca files", root_review_html)
        self.assertIn("minecraft-test-world\\verification-checklist.txt", root_review_html)
        self.assertIn("Anchor-focused shell starts", root_review_html)
        self.assertIn('--focus-anchor &quot;arrival&quot;', root_review_html)
        self.assertIn("minecraft-test-world-harbor-town-arrival", root_review_html)
        self.assertIn("first-map-test-world", root_review_html)
        self.assertIn("--max-side 128", root_review_html)
        self.assertIn("verification-checklist.txt", root_review_html)
        self.assertIn("First map:", summary)
        self.assertIn("- root review: review.html", summary)
        self.assertIn("Logical world size: 2048 x 1536", summary)
        self.assertIn("World scale: Local district", summary)
        self.assertIn("Preset story: A cinematic coast-to-mountain story space", summary)
        self.assertIn("Key regions: Harbor Town, Salt Coast, Old Pine Forest, +2 more", summary)
        self.assertIn("Scale bridge: 1 px = 8 blocks", summary)
        self.assertIn("Open first: review.html", summary)

    def test_summarize_project_first_map_status_reads_manifest_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "status-world"
            write_project_first_map(
                project_dir,
                "Status World",
                2048,
                1536,
                "coastal-valley",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            result = summarize_project_first_map_status(project_dir)
            summary = format_project_first_map_status_result(result)

        self.assertEqual(result.preset_name, "coastal-valley")
        self.assertEqual(result.world_scale_label, "Local district")
        self.assertIn("Good for one town plus nearby coast", result.world_scale_summary)
        self.assertIn("comfortable for local travel beats", result.world_scale_planning_note)
        self.assertIn("A cinematic coast-to-mountain story space", result.preset_story)
        self.assertEqual(result.key_regions[:3], ("Harbor Town", "Salt Coast", "Old Pine Forest"))
        self.assertEqual(result.size_edit_config_path, project_dir / "titanforge.toml")
        self.assertEqual(result.size_edit_options[0].label, "Smaller test map")
        self.assertEqual(result.size_edit_options[0].width, 256)
        self.assertEqual(result.size_edit_options[0].length, 192)
        self.assertEqual(result.size_edit_options[1].scale_label, "Local district")
        self.assertIn('--width 16000 --length 12000', result.size_edit_options[-1].rerun_command)
        self.assertEqual(result.open_sequence[0], ("root-review", "review.html"))
        self.assertIn(("presetCatalog", "py -3.11 -m titanforge preset-catalog"), result.commands)
        self.assertIn(('buildTestWorld', 'py -3.11 -m titanforge first-map-test-world "status-world" --max-side 128'), result.commands)
        self.assertEqual(result.route_preview_path, project_dir / "first-map" / "draft" / "route-preview.png")
        self.assertEqual(result.route_plan_path, project_dir / "first-map" / "draft" / "route-plan.json")
        self.assertEqual(result.route_handoffs[0].route_id, "region-00")
        self.assertEqual(result.route_handoffs[0].kind, "intra-region")
        self.assertIn("Harbor Town / arrival -> Harbor Town / center", result.route_handoffs[0].summary)
        self.assertIn('--focus-anchor "arrival"', result.route_handoffs[0].start_command)
        self.assertEqual(result.route_handoffs[0].start_output_dir, "minecraft-test-world-harbor-town-arrival")
        self.assertIn('--focus-anchor "center"', result.route_handoffs[0].end_command)
        self.assertEqual(result.route_handoffs[0].end_output_dir, "minecraft-test-world-harbor-town-center")
        self.assertEqual(result.recommended_walkthrough[0].step_id, "step-01")
        self.assertEqual(result.recommended_walkthrough[0].title, "Start here")
        self.assertIn("Harbor Town", result.recommended_walkthrough[0].summary)
        self.assertIn('--focus-anchor "arrival"', result.recommended_walkthrough[0].command)
        self.assertEqual(result.recommended_walkthrough[0].output_dir, "minecraft-test-world-harbor-town-arrival")
        self.assertEqual(result.recommended_walkthrough[-1].title, "Final reveal")
        self.assertIn("Broken Ridge", result.recommended_walkthrough[-1].summary)
        self.assertEqual(
            result.next_actions[0],
            (
                "rerun-project-location",
                "After editing the config, rerun project-location to refresh the first map outputs.",
                'py -3.11 -m titanforge project-location "titanforge.toml" "first-map" --use-cleanup-for-heightmap',
            ),
        )
        self.assertEqual(result.minecraft_review_order[0][0], "fixture-summary")
        self.assertEqual(result.test_world_output_dir, "minecraft-test-world")
        self.assertEqual(result.test_world_recommended_max_side, 128)
        self.assertIn("128 x 128 sampled window", result.test_world_strategy_summary)
        self.assertEqual(result.test_world_recommended_region_file_count, 1)
        self.assertEqual(
            result.test_world_region_file_summary,
            "The starter sample should write 1 sampled .mca file under test-world\\region\\.",
        )
        self.assertEqual(result.test_world_first_multi_region_max_side, 1024)
        self.assertEqual(result.test_world_first_multi_region_file_count, 4)
        self.assertIn("--max-side 1024", result.test_world_multi_region_summary)
        self.assertIn("4 sampled .mca files", result.test_world_multi_region_summary)
        self.assertIn("disposable centered sample", result.recommended_manual_start.summary)
        self.assertEqual(result.recommended_manual_start.install_extra_command, "py -3.11 -m pip install -e .[donor-spikes]")
        self.assertEqual(result.recommended_manual_start.build_command, 'py -3.11 -m titanforge first-map-test-world "status-world" --max-side 128')
        self.assertEqual(result.recommended_manual_start.output_dir, "minecraft-test-world")
        self.assertEqual(result.recommended_manual_start.checklist_path, "minecraft-test-world\\verification-checklist.txt")
        self.assertEqual(result.recommended_manual_start.status_command, 'py -3.11 -m titanforge anvil-test-world-status "minecraft-test-world"')
        self.assertEqual(result.test_world_focus_commands[0][0], "Harbor Town")
        self.assertIn('--focus-region "Harbor Town"', result.test_world_focus_commands[0][1])
        self.assertEqual(result.test_world_focus_commands[0][2], "minecraft-test-world-harbor-town")
        self.assertIn('anvil-test-world-status "minecraft-test-world-harbor-town"', result.test_world_focus_commands[0][3])
        self.assertEqual(result.test_world_focus_anchor_commands[0][0], "Harbor Town / arrival")
        self.assertIn('--focus-anchor "arrival"', result.test_world_focus_anchor_commands[0][1])
        self.assertEqual(result.test_world_focus_anchor_commands[0][2], "minecraft-test-world-harbor-town-arrival")
        self.assertIn('anvil-test-world-status "minecraft-test-world-harbor-town-arrival"', result.test_world_focus_anchor_commands[0][3])
        self.assertEqual(result.starter_test_verdict, "caution")
        self.assertIn("disposable first Minecraft test", result.starter_test_summary)
        self.assertIn("- location review: first-map\\location\\review.html", summary)
        self.assertIn("Preset intent:", summary)
        self.assertIn("Size guidance:", summary)
        self.assertIn("Change world size:", summary)
        self.assertIn("- edit titanforge.toml: width and length must stay between 64 and 32000 blocks.", summary)
        self.assertIn("- Smaller test map: 256 x 192", summary)
        self.assertIn("- Regional map: 8192 x 6144", summary)
        self.assertIn("- rerun example: py -3.11 -m titanforge first-map", summary)
        self.assertIn("Review now:", summary)
        self.assertIn("Story routes:", summary)
        self.assertIn("- route-preview: first-map\\draft\\route-preview.png", summary)
        self.assertIn("- route-plan: first-map\\draft\\route-plan.json", summary)
        self.assertIn("- recommended walkthrough:", summary)
        self.assertIn("- step-01: Start here (Open the first story entry point in Harbor Town.)", summary)
        self.assertIn("- walkthrough shell: py -3.11 -m titanforge first-map-test-world", summary)
        self.assertIn("minecraft-test-world-harbor-town-arrival", summary)
        self.assertIn("full route sample pairs", summary)
        self.assertIn("If you need changes:", summary)
        self.assertIn("Minecraft later:", summary)
        self.assertIn("starter-test-verdict: caution", summary)
        self.assertIn("- recommended first manual-open:", summary)
        self.assertIn("- summary: Start with one disposable centered sample before trying focused regions or larger manual-open passes.", summary)
        self.assertIn("- open next: minecraft-test-world\\verification-checklist.txt", summary)
        self.assertIn("sampled-test-strategy: start with --max-side 128", summary)
        self.assertIn("- starter sample scope: The starter sample should write 1 sampled .mca file under test-world\\region\\.", summary)
        self.assertIn("- growth scope: The first multi-file growth is --max-side 1024, which should write 4 sampled .mca files.", summary)
        self.assertIn("- focus samples:", summary)
        self.assertIn('--focus-region "Harbor Town"', summary)
        self.assertIn("folder: minecraft-test-world-harbor-town", summary)
        self.assertIn("- focus anchors:", summary)
        self.assertIn('--focus-anchor "arrival"', summary)
        self.assertIn("folder: minecraft-test-world-harbor-town-arrival", summary)
        self.assertIn("optional-test-world: Experimental manual-open shell only, not full world export.", summary)
        self.assertIn("Command hints:", summary)
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
        self.assertIn("Preset story: A layered island setting", stdout.getvalue())
        self.assertIn("Key regions: Crown Harbor, Stormwater Shore, Interior Canopy, +2 more", stdout.getvalue())
        self.assertIn("Scale bridge: 1 px =", stdout.getvalue())
        self.assertIn("Open first: review.html", stdout.getvalue())
        self.assertIn("Validation: 0 errors, 0 warnings", stdout.getvalue())

    def test_first_map_status_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "status-cli"
            write_project_first_map(
                project_dir,
                "Status CLI",
                1024,
                768,
                "frontier-basin",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["first-map-status", str(project_dir)])

        self.assertEqual(exit_code, 0)
        self.assertIn("First-map status:", stdout.getvalue())
        self.assertIn("- preset: frontier-basin", stdout.getvalue())
        self.assertIn("- root review: review.html", stdout.getvalue())
        self.assertIn("Preset intent:", stdout.getvalue())
        self.assertIn("Review now:", stdout.getvalue())
        self.assertIn("Minecraft later:", stdout.getvalue())
        self.assertIn("starter-test-verdict:", stdout.getvalue())
        self.assertIn("Command hints:", stdout.getvalue())
        self.assertIn("buildTestWorld", stdout.getvalue())

    def test_write_project_first_map_test_world_uses_manifest_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "manual-open"
            write_project_first_map(
                project_dir,
                "Manual Open",
                1024,
                768,
                "coastal-valley",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            result = write_project_first_map_test_world(
                project_dir,
                max_side=128,
                anvil_module=_FakeAnvilModule,
            )
            manifest = json.loads((result.output_dir / "anvil-test-world-manifest.json").read_text(encoding="utf-8"))
            checklist_exists = (result.output_dir / "verification-checklist.txt").exists()

        self.assertEqual(result.output_dir.name, "minecraft-test-world")
        self.assertEqual(manifest["project"]["name"], "Manual Open")
        self.assertEqual(manifest["sampleWindow"]["size"]["width"], 128)
        self.assertTrue(checklist_exists)

    def test_write_project_first_map_test_world_can_focus_named_region(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "focused-wrapper"
            write_project_first_map(
                project_dir,
                "Focused Wrapper",
                2048,
                1536,
                "coastal-valley",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            result = write_project_first_map_test_world(
                project_dir,
                max_side=128,
                focus_region_title="Broken Ridge",
                anvil_module=_FakeAnvilModule,
            )
            manifest = json.loads((result.output_dir / "anvil-test-world-manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["sampleWindow"]["origin"]["x"], 1728)
        self.assertEqual(manifest["sampleWindow"]["origin"]["z"], 208)
        self.assertEqual(manifest["sampleWindow"]["focusRegion"], "Broken Ridge")
        self.assertEqual(result.output_dir.name, "minecraft-test-world-broken-ridge")
        self.assertIn(
            '--focus-region "Broken Ridge"',
            manifest["sampleGrowth"]["rerunCurrentCommand"],
        )

    def test_write_project_first_map_test_world_can_focus_named_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "anchor-wrapper"
            write_project_first_map(
                project_dir,
                "Anchor Wrapper",
                2048,
                1536,
                "coastal-valley",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            result = write_project_first_map_test_world(
                project_dir,
                max_side=128,
                focus_region_title="Broken Ridge",
                focus_anchor_id="ridge-vista",
                anvil_module=_FakeAnvilModule,
            )
            manifest = json.loads((result.output_dir / "anvil-test-world-manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["sampleWindow"]["focusAnchor"], "ridge-vista")
        self.assertEqual(result.output_dir.name, "minecraft-test-world-broken-ridge-ridge-vista")
        self.assertIn(
            '--focus-anchor "ridge-vista"',
            manifest["sampleGrowth"]["rerunCurrentCommand"],
        )

    def test_focused_test_world_runs_can_coexist_in_distinct_output_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "coexisting-wrapper"
            write_project_first_map(
                project_dir,
                "Coexisting Wrapper",
                2048,
                1536,
                "coastal-valley",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            harbor_result = write_project_first_map_test_world(
                project_dir,
                max_side=128,
                focus_region_title="Harbor Town",
                anvil_module=_FakeAnvilModule,
            )
            ridge_result = write_project_first_map_test_world(
                project_dir,
                max_side=128,
                focus_region_title="Broken Ridge",
                focus_anchor_id="ridge-vista",
                anvil_module=_FakeAnvilModule,
            )
            harbor_manifest_exists = harbor_result.manifest_path.exists()
            ridge_manifest_exists = ridge_result.manifest_path.exists()

        self.assertEqual(harbor_result.output_dir.name, "minecraft-test-world-harbor-town")
        self.assertEqual(ridge_result.output_dir.name, "minecraft-test-world-broken-ridge-ridge-vista")
        self.assertTrue(harbor_manifest_exists)
        self.assertTrue(ridge_manifest_exists)

    def test_write_project_first_map_test_world_uses_recommended_sample_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "auto-sample"
            write_project_first_map(
                project_dir,
                "Auto Sample",
                8192,
                4096,
                "frontier-basin",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            result = write_project_first_map_test_world(
                project_dir,
                anvil_module=_FakeAnvilModule,
            )
            manifest = json.loads((result.output_dir / "anvil-test-world-manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["sampleWindow"]["size"]["width"], 64)
        self.assertEqual(manifest["sampleWindow"]["size"]["length"], 64)

    def test_first_map_test_world_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "cli-shell"
            write_project_first_map(
                project_dir,
                "CLI Shell",
                1024,
                768,
                "frontier-basin",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            stdout = io.StringIO()

            with mock.patch("titanforge.spikes.anvil_region._load_anvil_module", return_value=_FakeAnvilModule):
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(["first-map-test-world", str(project_dir), "--max-side", "128"])

            manifest_exists = (project_dir / "minecraft-test-world" / "anvil-test-world-manifest.json").exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(manifest_exists)
        self.assertIn("Anvil test world:", stdout.getvalue())
        self.assertIn("Open next: verification-checklist.txt", stdout.getvalue())

    def test_first_map_test_world_cli_uses_recommended_sample_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "cli-auto-shell"
            write_project_first_map(
                project_dir,
                "CLI Auto Shell",
                8192,
                4096,
                "frontier-basin",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            stdout = io.StringIO()

            with mock.patch("titanforge.spikes.anvil_region._load_anvil_module", return_value=_FakeAnvilModule):
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(["first-map-test-world", str(project_dir)])

            manifest = json.loads(
                (project_dir / "minecraft-test-world" / "anvil-test-world-manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(manifest["sampleWindow"]["size"]["width"], 64)
        self.assertEqual(manifest["sampleWindow"]["size"]["length"], 64)
        self.assertEqual(manifest["sampleGrowth"]["nextMaxSide"], 128)
        self.assertIn('py -3.11 -m titanforge first-map-test-world', manifest["sampleGrowth"]["nextSampleCommand"])
        self.assertIn('py -3.11 -m titanforge first-map-status', manifest["originHandoff"]["projectStatusCommand"])

    def test_first_map_test_world_failed_status_points_back_to_project_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory) / "failed-wrapper"
            write_project_first_map(
                project_dir,
                "Failed Wrapper",
                2048,
                1536,
                "coastal-valley",
                max_draft_side=256,
                use_cleanup_for_heightmap=True,
            )
            with mock.patch("titanforge.spikes.anvil_region._load_anvil_module", return_value=_FakeAnvilModule):
                exit_code = main(["first-map-test-world", str(project_dir), "--max-side", "128"])
            update_test_world_verification_report(
                project_dir / "minecraft-test-world" / "verification-report.json",
                check_id="minecraft-open",
                check_status="failed",
                check_note="Client did not open the sample cleanly.",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                status_exit_code = main(["anvil-test-world-status", str(project_dir / "minecraft-test-world")])

        self.assertEqual(exit_code, 0)
        self.assertEqual(status_exit_code, 0)
        self.assertIn("- decision: stop sample growth and fix the current map direction first.", stdout.getvalue())
        self.assertIn("- go back to project handoff: py -3.11 -m titanforge first-map-status", stdout.getvalue())

    def test_first_map_test_world_strategy_helpers(self) -> None:
        self.assertEqual(suggest_first_map_test_world_max_side(192, 128), 192)
        self.assertEqual(suggest_first_map_test_world_max_side(1024, 768), 256)
        self.assertEqual(suggest_first_map_test_world_max_side(2048, 1536), 128)
        self.assertEqual(suggest_first_map_test_world_max_side(8192, 4096), 64)
        strategy = build_first_map_test_world_strategy(2048, 1536)
        self.assertEqual(strategy["recommendedMaxSide"], 128)
        self.assertIn("128 x 128 sampled window", strategy["summary"])
        self.assertEqual(strategy["recommendedRegionFileCount"], 1)
        self.assertEqual(strategy["firstMultiRegionMaxSide"], 1024)
        self.assertEqual(strategy["firstMultiRegionRegionFileCount"], 4)
        self.assertIn("1 sampled .mca file", strategy["regionFileSummary"])
        self.assertIn("4 sampled .mca files", strategy["multiRegionSummary"])
        small_strategy = build_first_map_test_world_strategy(192, 128)
        self.assertEqual(small_strategy["recommendedRegionFileCount"], 1)
        self.assertIsNone(small_strategy["firstMultiRegionMaxSide"])
        self.assertIn("one sampled .mca file", small_strategy["multiRegionSummary"])
