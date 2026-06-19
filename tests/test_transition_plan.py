from pathlib import Path
import tempfile
import unittest

from titanforge.core.project import load_project_config
from titanforge.core.transition_plan import build_transition_plan, render_transition_preview
from titanforge.core.world_plan import build_world_plan
from titanforge.masks.png import read_png


class TransitionPlanTests(unittest.TestCase):
    def test_build_transition_plan_creates_neighbor_spans(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)

        transition_plan = build_transition_plan(world_plan)

        kinds = {transition.kind for transition in transition_plan.transitions}
        self.assertEqual(transition_plan.width, 512)
        self.assertEqual(transition_plan.length, 512)
        self.assertEqual(len(transition_plan.transitions), 4)
        self.assertIn("coast-transition", kinds)
        self.assertIn("treeline-rise", kinds)
        self.assertIn("settled-edge", kinds)

    def test_render_transition_preview_creates_png(self) -> None:
        config = load_project_config(Path("examples/tiny_project/titanforge.toml"))
        world_plan = build_world_plan(config)
        transition_plan = build_transition_plan(world_plan)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "transition-preview.png"
            render_transition_preview(
                transition_plan,
                output_path,
                raster_width=256,
                raster_length=256,
                blocks_per_pixel=2,
            )
            image = read_png(output_path)

        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        non_background = sum(1 for row in image.pixels for pixel in row if pixel != (240, 236, 226, 255))
        self.assertGreater(non_background, 0)
