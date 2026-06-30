from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from titanforge.cli import main
from titanforge.core.project import load_project_config, ProjectConfig, ProjectRegion
from titanforge.spikes.anvil_region import write_anvil_region_spike


class _FakeBlock:
    def __init__(self, namespace: str, block_id: str = "air", properties: dict[str, str] | None = None) -> None:
        self.namespace = namespace
        self.id = block_id
        self.properties = dict(properties or {})


class _FakeEmptyRegion:
    def __init__(self, x: int, z: int) -> None:
        self.x = x
        self.z = z
        self.blocks: dict[tuple[int, int, int], _FakeBlock] = {}

    def set_block(self, block: _FakeBlock, x: int, y: int, z: int) -> None:
        expected_region_x = x // 512
        expected_region_z = z // 512
        if expected_region_x != self.x or expected_region_z != self.z:
            raise ValueError(f"Block ({x}, {y}, {z}) is outside fake region {self.x}, {self.z}")
        self.blocks[(x, y, z)] = _FakeBlock(block.namespace, block.id, block.properties)

    def save(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "region": {"x": self.x, "z": self.z},
            "blocks": [
                {
                    "x": x,
                    "y": y,
                    "z": z,
                    "namespace": block.namespace,
                    "id": block.id,
                    "properties": block.properties,
                }
                for (x, y, z), block in sorted(self.blocks.items())
            ]
        }
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class _FakeRegion:
    def __init__(self, x: int, z: int, blocks: dict[tuple[int, int, int], _FakeBlock]) -> None:
        self.x = x
        self.z = z
        self.blocks = blocks

    @classmethod
    def from_file(cls, path: str) -> "_FakeRegion":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        region = payload["region"]
        blocks = {
            (entry["x"], entry["y"], entry["z"]): _FakeBlock(
                entry["namespace"],
                entry["id"],
                entry["properties"],
            )
            for entry in payload["blocks"]
        }
        return cls(region["x"], region["z"], blocks)


class _FakeChunk:
    def __init__(self, region: _FakeRegion, chunk_x: int, chunk_z: int) -> None:
        self._region = region
        self._chunk_x = chunk_x
        self._chunk_z = chunk_z

    @classmethod
    def from_region(cls, region: _FakeRegion, chunk_x: int, chunk_z: int) -> "_FakeChunk":
        return cls(region, chunk_x, chunk_z)

    def get_block(self, x: int, y: int, z: int) -> _FakeBlock:
        global_x = self._region.x * 512 + self._chunk_x * 16 + x
        global_z = self._region.z * 512 + self._chunk_z * 16 + z
        return self._region.blocks.get((global_x, y, global_z), _FakeBlock("minecraft", "air"))


class _FakeAnvilModule:
    EmptyRegion = _FakeEmptyRegion
    Region = _FakeRegion
    Chunk = _FakeChunk
    Block = _FakeBlock


class AnvilRegionSpikeTests(unittest.TestCase):
    def test_write_anvil_region_spike_creates_manifest_and_region_artifact(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "anvil-spike"
            result = write_anvil_region_spike(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            manifest = json.loads((output_dir / "anvil-region-spike-manifest.json").read_text(encoding="utf-8"))
            readme_text = (output_dir / "README.txt").read_text(encoding="utf-8")
            region_exists = result.region_path.exists()

        self.assertEqual(result.region_path, output_dir / "region" / "r.0.0.mca")
        self.assertTrue(region_exists)
        self.assertEqual(manifest["schema"], "titanforge.spike.anvil-region")
        self.assertEqual(manifest["artifacts"]["regionFile"], "region\\r.0.0.mca")
        self.assertEqual(manifest["artifacts"]["regionFiles"], ["region\\r.0.0.mca"])
        self.assertEqual(manifest["artifacts"]["regionFileCount"], 1)
        self.assertEqual(manifest["sampleWindow"]["size"]["width"], 128)
        self.assertEqual(manifest["sampleWindow"]["cropped"], True)
        self.assertTrue(manifest["verification"]["allMatched"])
        self.assertIn("anvil-parser2", readme_text)
        self.assertIn("one narrow write/read path", readme_text)

    def test_write_anvil_region_spike_can_span_multiple_region_files(self) -> None:
        config = ProjectConfig(
            name="Wide Harbor Province",
            target_version="1.21.11",
            width=1024,
            length=1024,
            premise="A broad starter province for multi-region export tests.",
            player_experience="The player should feel the world widening beyond one local district.",
            regions=(
                ProjectRegion(
                    title="South Bay",
                    kind="sea",
                    story_role="arrival",
                    mood="open",
                    coverage_hint="50%",
                    notes="Wide coastal water.",
                ),
                ProjectRegion(
                    title="North Reach",
                    kind="settlement",
                    story_role="destination",
                    mood="busy",
                    coverage_hint="50%",
                    notes="Large inland buildable shelf.",
                ),
            ),
            pipeline=("preview",),
        )

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "multi-region-spike"
            result = write_anvil_region_spike(config, output_dir, max_side=1024, anvil_module=_FakeAnvilModule)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            readme_text = result.readme_path.read_text(encoding="utf-8")

        self.assertEqual(result.region_file_count, 4)
        self.assertEqual(tuple(path.name for path in result.region_paths), ("r.0.0.mca", "r.0.1.mca", "r.1.0.mca", "r.1.1.mca"))
        self.assertEqual(manifest["artifacts"]["regionFileCount"], 4)
        self.assertEqual(manifest["artifacts"]["regionFiles"][0], "region\\r.0.0.mca")
        self.assertIn("region\\r.1.1.mca", manifest["artifacts"]["regionFiles"])
        self.assertIn("Region files: 4 under region\\", readme_text)

    def test_write_anvil_region_spike_keeps_small_world_uncropped(self) -> None:
        config = ProjectConfig(
            name="Small Draft",
            target_version="1.21.11",
            width=96,
            length=96,
            premise="Small sample world.",
            player_experience="The player should feel oriented.",
            regions=(
                ProjectRegion(
                    title="Harbor",
                    kind="port",
                    story_role="arrival",
                    mood="busy",
                    coverage_hint="100%",
                    notes="Stone quay and water edge.",
                ),
            ),
            pipeline=("preview",),
        )

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "anvil-spike"
            result = write_anvil_region_spike(config, output_dir, max_side=128, anvil_module=_FakeAnvilModule)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.sampled_width, 96)
        self.assertEqual(result.sampled_length, 96)
        self.assertFalse(result.cropped)
        self.assertEqual(manifest["sampleWindow"]["cropped"], False)

    def test_write_anvil_region_spike_can_focus_named_region(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "focused-spike"
            result = write_anvil_region_spike(
                config,
                output_dir,
                max_side=128,
                focus_region_title="Old Pine Forest",
                anvil_module=_FakeAnvilModule,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            readme_text = result.readme_path.read_text(encoding="utf-8")

        self.assertEqual(result.origin_x, 208)
        self.assertEqual(result.origin_z, 192)
        self.assertEqual(result.focus_region_title, "Old Pine Forest")
        self.assertEqual(manifest["sampleWindow"]["origin"]["x"], 208)
        self.assertEqual(manifest["sampleWindow"]["origin"]["z"], 192)
        self.assertEqual(manifest["sampleWindow"]["focusRegion"], "Old Pine Forest")
        self.assertIn('Focus region: "Old Pine Forest"', readme_text)

    def test_write_anvil_region_spike_can_focus_named_anchor(self) -> None:
        config = load_project_config(Path("examples") / "tiny_project" / "titanforge.toml")

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "anchor-spike"
            result = write_anvil_region_spike(
                config,
                output_dir,
                max_side=128,
                focus_region_title="Broken Ridge",
                focus_anchor_id="ridge-vista",
                anvil_module=_FakeAnvilModule,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.origin_x, 336)
        self.assertEqual(result.origin_z, 16)
        self.assertEqual(result.focus_region_title, "Broken Ridge")
        self.assertEqual(result.focus_anchor_id, "ridge-vista")
        self.assertEqual(manifest["sampleWindow"]["focusAnchor"], "ridge-vista")

    def test_anvil_region_spike_cli_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "anvil-spike"
            stdout = io.StringIO()

            with mock.patch("titanforge.spikes.anvil_region._load_anvil_module", return_value=_FakeAnvilModule):
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "anvil-region-spike",
                            str(Path("examples") / "tiny_project" / "titanforge.toml"),
                            str(output_dir),
                            "--max-side",
                            "128",
                        ]
                    )

            manifest_exists = (output_dir / "anvil-region-spike-manifest.json").exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(manifest_exists)
        self.assertIn("Anvil region spike:", stdout.getvalue())
        self.assertIn("- region files: 1", stdout.getvalue())
        self.assertIn("- first region file: r.0.0.mca", stdout.getvalue())

    def test_anvil_region_spike_cli_rejects_unaligned_sample_size(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "anvil-region-spike",
                    str(Path("examples") / "tiny_project" / "titanforge.toml"),
                    "out\\bad-anvil-spike",
                    "--max-side",
                    "130",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("--max-side must be divisible by 16", stderr.getvalue())
