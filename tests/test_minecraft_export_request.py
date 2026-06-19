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
from titanforge.exporters.minecraft_12111_request import build_minecraft_export_request, write_minecraft_export_request


class MinecraftExportRequestTests(unittest.TestCase):
    def test_build_request_supports_12111(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        request = build_minecraft_export_request("1.21.11", world_plan, transition_plan, road_plan, settlement_plan)

        self.assertTrue(request.supported)
        self.assertEqual(request.export_mode, "schematic-fixture")
        self.assertEqual(len(request.region_bands), len(world_plan.regions))
        self.assertEqual(len(request.transition_bands), len(transition_plan.transitions))
        self.assertEqual(len(request.road_strips), len(road_plan.roads))
        self.assertEqual(len(request.settlement_pads), len(settlement_plan.blockouts))
        self.assertEqual(request.road_strips[0].operation, "path-strip")

    def test_build_request_marks_unsupported_targets(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        request = build_minecraft_export_request("1.12.2", world_plan, transition_plan, road_plan, settlement_plan)

        self.assertFalse(request.supported)
        self.assertEqual(request.export_mode, "unsupported")
        self.assertEqual(request.region_bands, ())
        self.assertIn("No export request adapter is implemented yet", request.notes[-1])

    def test_write_request_creates_json(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "export-request.json"
            write_minecraft_export_request("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_path)

            self.assertTrue(output_path.exists())
