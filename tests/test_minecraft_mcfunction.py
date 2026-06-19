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
from titanforge.exporters.minecraft_12111_block_fixture import build_minecraft_block_fixture
from titanforge.exporters.minecraft_12111_mcfunction import build_mcfunction_lines, write_minecraft_mcfunction_fixture


class MinecraftMcfunctionTests(unittest.TestCase):
    def test_build_mcfunction_lines_supports_12111(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)
        fixture = build_minecraft_block_fixture("1.21.11", world_plan, transition_plan, road_plan, settlement_plan)

        lines = build_mcfunction_lines(fixture)

        self.assertTrue(any(line.startswith("fill ") for line in lines))
        self.assertTrue(any("region-band" in line for line in lines if line.startswith("#")))

    def test_build_mcfunction_lines_chunks_large_cuboids(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)
        fixture = build_minecraft_block_fixture("1.21.11", world_plan, transition_plan, road_plan, settlement_plan)

        lines = build_mcfunction_lines(fixture)
        self.assertIn("fill 0 64 0 76 66 31 oak_planks", lines)
        self.assertIn("fill 0 64 32 76 66 63 oak_planks", lines)

    def test_write_mcfunction_fixture_creates_file(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "place-fixture.mcfunction"
            write_minecraft_mcfunction_fixture("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_path)

            self.assertTrue(output_path.exists())
