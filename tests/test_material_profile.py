from pathlib import Path
import tempfile
import unittest

from titanforge.core.placement_plan import build_placement_plan
from titanforge.core.project import load_project_config
from titanforge.core.road_plan import build_road_plan
from titanforge.core.settlement_plan import build_settlement_plan
from titanforge.core.transition_plan import build_transition_plan
from titanforge.core.world_plan import build_world_plan
from titanforge.versions.material_profile import build_material_profile, write_material_profile
from titanforge.core.route_plan import build_route_plan


class MaterialProfileTests(unittest.TestCase):
    def test_build_material_profile_supports_12111(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        profile = build_material_profile("1.21.11", world_plan, transition_plan, road_plan, settlement_plan)

        self.assertTrue(profile.supported)
        self.assertEqual(len(profile.region_materials), len(world_plan.regions))
        self.assertEqual(len(profile.transition_materials), len(transition_plan.transitions))
        self.assertEqual(len(profile.road_materials), len(road_plan.roads))
        self.assertEqual(len(profile.settlement_materials), len(settlement_plan.blockouts))
        self.assertEqual(profile.region_materials[0].primary_block, "oak_planks")

    def test_build_material_profile_marks_unsupported_targets(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        profile = build_material_profile("1.12.2", world_plan, transition_plan, road_plan, settlement_plan)

        self.assertFalse(profile.supported)
        self.assertEqual(profile.region_materials, ())
        self.assertIn("No material adapter is implemented yet", profile.notes[0])

    def test_write_material_profile_creates_json(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "material-profile.json"
            write_material_profile("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_path)

            self.assertTrue(output_path.exists())
