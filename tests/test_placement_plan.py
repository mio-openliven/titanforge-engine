from pathlib import Path
import tempfile
import unittest

from titanforge.core.placement_plan import build_placement_plan, render_placement_preview
from titanforge.core.project import load_project_config
from titanforge.core.route_plan import build_route_plan
from titanforge.core.world_plan import build_world_plan
from titanforge.masks.png import read_png


class PlacementPlanTests(unittest.TestCase):
    def test_build_placement_plan_creates_anchor_and_route_sites(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        route_plan = build_route_plan(world_plan)

        placement_plan = build_placement_plan(world_plan, route_plan)

        kinds = {site.kind for site in placement_plan.sites}
        self.assertEqual(placement_plan.width, 512)
        self.assertEqual(placement_plan.length, 512)
        self.assertIn("entry-plaza", kinds)
        self.assertIn("dock-edge", kinds)
        self.assertIn("overlook", kinds)
        self.assertIn("route-junction", kinds)

    def test_render_placement_preview_creates_png(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        route_plan = build_route_plan(world_plan)
        placement_plan = build_placement_plan(world_plan, route_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "placement-preview.png"
            render_placement_preview(
                route_plan,
                placement_plan,
                output_path,
                raster_width=256,
                raster_length=256,
                blocks_per_pixel=2,
            )
            image = read_png(output_path)

        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        non_background = sum(1 for row in image.pixels for pixel in row if pixel != (239, 233, 220, 255))
        self.assertGreater(non_background, 0)
