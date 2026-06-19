from pathlib import Path
import json
import tempfile
import unittest

from titanforge.core.project import load_project_config
from titanforge.core.route_plan import build_route_plan, render_route_preview, route_plan_to_dict
from titanforge.core.world_plan import build_world_plan
from titanforge.masks.png import read_png


class RoutePlanTests(unittest.TestCase):
    def test_build_route_plan_creates_region_and_transition_routes(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)

        route_plan = build_route_plan(world_plan)

        self.assertEqual(route_plan.width, 512)
        self.assertEqual(route_plan.length, 512)
        self.assertEqual(len(route_plan.routes), 9)
        self.assertEqual(route_plan.routes[0].kind, "intra-region")
        self.assertEqual(route_plan.routes[-1].kind, "transition")

    def test_render_route_preview_creates_png(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        route_plan = build_route_plan(world_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "route-preview.png"
            render_route_preview(route_plan, output_path, raster_width=256, raster_length=256, blocks_per_pixel=2)
            image = read_png(output_path)

        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        non_background = sum(1 for row in image.pixels for pixel in row if pixel != (243, 236, 221, 255))
        self.assertGreater(non_background, 0)
