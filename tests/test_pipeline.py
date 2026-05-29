import unittest

from titanforge.pipeline.stage import Pipeline, StageResult


class FakeStage:
    name = "fake"

    def run(self) -> StageResult:
        return StageResult(name=self.name, artifacts=("preview.txt",), notes=("ok",))


class PipelineTests(unittest.TestCase):
    def test_pipeline_runs_stages_in_order(self) -> None:
        result = Pipeline(stages=[FakeStage()]).run()

        self.assertEqual(result, [StageResult(name="fake", artifacts=("preview.txt",), notes=("ok",))])
