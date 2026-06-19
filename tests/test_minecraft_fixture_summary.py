import json
from pathlib import Path
import tempfile
import unittest

from titanforge.core.placement_plan import build_placement_plan
from titanforge.core.project import load_project_config
from titanforge.core.road_plan import build_road_plan
from titanforge.core.route_plan import build_route_plan
from titanforge.core.settlement_plan import build_settlement_plan
from titanforge.core.transition_plan import build_transition_plan
from titanforge.core.world_plan import build_world_plan
from titanforge.exporters.minecraft_12111_fixture_summary import write_minecraft_fixture_summary


class MinecraftFixtureSummaryTests(unittest.TestCase):
    def test_write_fixture_summary_creates_json(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "fixture-summary.json"
            write_minecraft_fixture_summary("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_path)
            summary = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["adapter"]["targetVersion"], "1.21.11")
        self.assertEqual(summary["adapter"]["supported"], True)
        self.assertEqual(summary["functionIds"]["place"], "titanforge:place_fixture")
        self.assertEqual(summary["functionIds"]["clear"], "titanforge:clear_fixture")
        self.assertGreater(summary["counts"]["cuboids"], 0)
        self.assertGreater(summary["counts"]["placeFillCommands"], 0)
        self.assertEqual(summary["counts"]["placeFillCommands"], summary["counts"]["clearFillCommands"])
        self.assertGreater(summary["bounds"]["width"], 0)
        self.assertGreater(summary["bounds"]["length"], 0)
