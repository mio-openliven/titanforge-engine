from pathlib import Path
import tempfile
import unittest

from titanforge.core.placement_plan import build_placement_plan
from titanforge.core.project import load_project_config
from titanforge.core.road_plan import build_road_plan, render_road_preview
from titanforge.core.route_plan import build_route_plan
from titanforge.core.world_plan import build_world_plan
from titanforge.masks.png import read_png


class RoadPlanTests(unittest.TestCase):
    def test_build_road_plan_creates_main_and_local_segments(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)

        road_plan = build_road_plan(route_plan, placement_plan)

        kinds = {road.kind for road in road_plan.roads}
        widths = {road.width_hint for road in road_plan.roads}
        self.assertEqual(road_plan.width, 512)
        self.assertEqual(road_plan.length, 512)
        self.assertIn("main-road", kinds)
        self.assertIn("local-path", kinds)
        self.assertIn("wide", widths)
        self.assertIn("narrow", widths)

    def test_render_road_preview_creates_png(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)
        road_plan = build_road_plan(route_plan, placement_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "road-preview.png"
            render_road_preview(road_plan, placement_plan, output_path, raster_width=256, raster_length=256, blocks_per_pixel=2)
            image = read_png(output_path)

        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        non_background = sum(1 for row in image.pixels for pixel in row if pixel != (233, 227, 214, 255))
        self.assertGreater(non_background, 0)
