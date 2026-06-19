from __future__ import annotations

import json
from pathlib import Path
import zipfile

from titanforge.core.road_plan import RoadPlan
from titanforge.core.settlement_plan import SettlementPlan
from titanforge.core.transition_plan import TransitionPlan
from titanforge.core.world_plan import WorldPlan
from titanforge.exporters.minecraft_12111_block_fixture import build_minecraft_block_fixture
from titanforge.exporters.minecraft_12111_mcfunction import build_clear_mcfunction_lines, build_mcfunction_lines


DATAPACK_MIN_FORMAT = [94, 1]
DATAPACK_MAX_FORMAT = [94, 1]
PLACE_FUNCTION_ID = "titanforge:place_fixture"
CLEAR_FUNCTION_ID = "titanforge:clear_fixture"


def write_minecraft_datapack_fixture(
    target_version: str,
    world_plan: WorldPlan,
    transition_plan: TransitionPlan,
    road_plan: RoadPlan,
    settlement_plan: SettlementPlan,
    output_dir: Path,
) -> Path:
    fixture = build_minecraft_block_fixture(target_version, world_plan, transition_plan, road_plan, settlement_plan)
    pack_dir = output_dir
    function_path = pack_dir / "data" / "titanforge" / "function" / "place_fixture.mcfunction"
    clear_function_path = pack_dir / "data" / "titanforge" / "function" / "clear_fixture.mcfunction"
    pack_meta_path = pack_dir / "pack.mcmeta"
    readme_path = pack_dir / "README.txt"

    function_path.parent.mkdir(parents=True, exist_ok=True)
    pack_meta_path.parent.mkdir(parents=True, exist_ok=True)

    pack_meta = {
        "pack": {
            "description": _pack_description(fixture.target_version, fixture.supported),
            "min_format": DATAPACK_MIN_FORMAT,
            "max_format": DATAPACK_MAX_FORMAT,
        }
    }
    pack_meta_path.write_text(json.dumps(pack_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    function_path.write_text("\n".join(build_mcfunction_lines(fixture)) + "\n", encoding="utf-8")
    clear_function_path.write_text("\n".join(build_clear_mcfunction_lines(fixture)) + "\n", encoding="utf-8")
    readme_path.write_text("\n".join(build_minecraft_datapack_readme_lines()) + "\n", encoding="utf-8")
    return pack_dir


def write_minecraft_datapack_fixture_zip(pack_dir: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(pack_dir.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(pack_dir))
    return output_path


def _pack_description(target_version: str, supported: bool) -> str:
    if supported:
        return "TitanForge 1.21.11 fixture pack"
    return f"TitanForge 1.21.11 fixture pack for unsupported requested target {target_version}"


def build_minecraft_fixture_command_lines() -> tuple[str, ...]:
    return (
        "TitanForge 1.21.11 fixture commands",
        "",
        "After copying the datapack into a world datapacks folder, run:",
        "/reload",
        f"/function {PLACE_FUNCTION_ID}",
        "",
        "To remove the same fixture again, run:",
        f"/function {CLEAR_FUNCTION_ID}",
    )


def build_minecraft_datapack_readme_lines() -> tuple[str, ...]:
    return (
        "TitanForge 1.21.11 fixture datapack",
        "",
        "1. Copy this datapack folder or datapack-fixture.zip into a Minecraft world datapacks folder.",
        "2. Open the world and run:",
        "   /reload",
        f"   /function {PLACE_FUNCTION_ID}",
        "",
        "To clear the same fixture again, run:",
        f"   /function {CLEAR_FUNCTION_ID}",
    )
