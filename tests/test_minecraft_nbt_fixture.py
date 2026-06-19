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
from titanforge.exporters.minecraft_12111_nbt_fixture import write_minecraft_nbt_fixture
from titanforge.exporters.nbt_codec import read_nbt


class MinecraftNbtFixtureTests(unittest.TestCase):
    def test_write_nbt_fixture_creates_binary_file(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "block-fixture.nbt"
            write_minecraft_nbt_fixture("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_path)
            root_name, payload = read_nbt(output_path.read_bytes())

        self.assertEqual(root_name, "TitanForgeFixture")
        self.assertEqual(payload["targetVersion"], "1.21.11")
        self.assertEqual(payload["supported"], True)
        self.assertGreater(len(payload["cuboids"]), 0)
