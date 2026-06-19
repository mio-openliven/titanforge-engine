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
from titanforge.exporters.minecraft_12111_chunk_plan import build_minecraft_chunk_plan, write_minecraft_chunk_plan


class MinecraftChunkPlanTests(unittest.TestCase):
    def test_build_chunk_plan_supports_12111(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        plan = build_minecraft_chunk_plan("1.21.11", world_plan, transition_plan, road_plan, settlement_plan)

        self.assertTrue(plan.supported)
        self.assertEqual(plan.chunk_size, 16)
        self.assertGreater(len(plan.coverages), 0)
        source_types = {coverage.source_type for coverage in plan.coverages}
        self.assertIn("region-band", source_types)
        self.assertIn("road-strip", source_types)
        self.assertIn("settlement-pad", source_types)

    def test_build_chunk_plan_marks_unsupported_targets(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        plan = build_minecraft_chunk_plan("1.12.2", world_plan, transition_plan, road_plan, settlement_plan)

        self.assertFalse(plan.supported)
        self.assertEqual(plan.coverages, ())
        self.assertIn("No chunk plan adapter is implemented yet", plan.notes[-1])

    def test_write_chunk_plan_creates_json(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "chunk-plan.json"
            write_minecraft_chunk_plan("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_path)

            self.assertTrue(output_path.exists())
