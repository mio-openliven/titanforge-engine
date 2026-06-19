import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from titanforge.core.placement_plan import build_placement_plan
from titanforge.core.project import load_project_config
from titanforge.core.road_plan import build_road_plan
from titanforge.core.route_plan import build_route_plan
from titanforge.core.settlement_plan import build_settlement_plan
from titanforge.core.transition_plan import build_transition_plan
from titanforge.core.world_plan import build_world_plan
from titanforge.exporters.minecraft_12111_datapack import write_minecraft_datapack_fixture, write_minecraft_datapack_fixture_zip


class MinecraftDatapackTests(unittest.TestCase):
    def test_write_datapack_fixture_creates_pack_structure(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "datapack-fixture"
            write_minecraft_datapack_fixture("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_dir)
            pack_meta = json.loads((output_dir / "pack.mcmeta").read_text(encoding="utf-8"))
            function_text = (output_dir / "data" / "titanforge" / "function" / "place_fixture.mcfunction").read_text(encoding="utf-8")
            clear_function_text = (output_dir / "data" / "titanforge" / "function" / "clear_fixture.mcfunction").read_text(encoding="utf-8")

        self.assertEqual(pack_meta["pack"]["min_format"], [94, 1])
        self.assertEqual(pack_meta["pack"]["max_format"], [94, 1])
        self.assertIn("TitanForge 1.21.11 fixture pack", pack_meta["pack"]["description"])
        self.assertIn("fill ", function_text)
        self.assertIn(" air", clear_function_text)

    def test_write_datapack_fixture_zip_creates_archive(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "datapack-fixture"
            zip_path = Path(directory) / "datapack-fixture.zip"
            write_minecraft_datapack_fixture("1.21.11", world_plan, transition_plan, road_plan, settlement_plan, output_dir)
            write_minecraft_datapack_fixture_zip(output_dir, zip_path)

            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())

        self.assertIn("pack.mcmeta", names)
        self.assertIn("data/titanforge/function/place_fixture.mcfunction", names)
        self.assertIn("data/titanforge/function/clear_fixture.mcfunction", names)
