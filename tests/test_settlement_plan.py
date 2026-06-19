from pathlib import Path
import tempfile
import unittest

from titanforge.core.placement_plan import build_placement_plan
from titanforge.core.project import load_project_config
from titanforge.core.road_plan import build_road_plan
from titanforge.core.route_plan import build_route_plan
from titanforge.core.settlement_plan import build_settlement_plan, render_settlement_preview
from titanforge.core.world_plan import build_world_plan
from titanforge.masks.png import read_png


class SettlementPlanTests(unittest.TestCase):
    def test_build_settlement_plan_creates_blockouts_from_sites(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)

        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        kinds = {blockout.kind for blockout in settlement_plan.blockouts}
        self.assertEqual(settlement_plan.width, 512)
        self.assertEqual(settlement_plan.length, 512)
        self.assertIn("gate", kinds)
        self.assertIn("core", kinds)
        self.assertIn("harbor", kinds)
        self.assertIn("junction", kinds)

    def test_render_settlement_preview_creates_png(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)
        settlement_plan = build_settlement_plan(placement_plan, road_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "settlement-preview.png"
            render_settlement_preview(
                settlement_plan,
                output_path,
                raster_width=256,
                raster_length=256,
                blocks_per_pixel=2,
            )
            image = read_png(output_path)

        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        non_background = sum(1 for row in image.pixels for pixel in row if pixel != (236, 230, 219, 255))
        self.assertGreater(non_background, 0)
