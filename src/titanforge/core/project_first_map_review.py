from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import TYPE_CHECKING

from titanforge.core.project_template import describe_world_scale

if TYPE_CHECKING:
    from titanforge.core.project_first_map import ProjectFirstMapResult
    from titanforge.core.project_first_map import build_first_map_test_world_strategy


def write_project_first_map_review_page(result: "ProjectFirstMapResult", output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_format_project_first_map_review_html(result), encoding="utf-8")
    return output_path


def _format_project_first_map_review_html(result: "ProjectFirstMapResult") -> str:
    scale = describe_world_scale(result.template_result.config.width, result.template_result.config.length)
    project_dir = result.project_dir
    config_path = result.template_result.config_path.relative_to(project_dir)
    location_review = result.location_result.location_result.review_page_path.relative_to(project_dir)
    draft_review = result.location_result.draft_result.review_page_path.relative_to(project_dir)
    route_plan = result.location_result.draft_result.route_plan_path.relative_to(project_dir)
    route_preview = result.location_result.draft_result.route_preview_path.relative_to(project_dir)
    fixture_summary = result.location_result.draft_result.fixture_summary_path.relative_to(project_dir)
    fixture_commands = result.location_result.draft_result.fixture_commands_path.relative_to(project_dir)
    datapack_zip = result.location_result.draft_result.datapack_fixture_zip_path.relative_to(project_dir)
    minecraft_first_pass = Path("minecraft-first-pass.txt")
    manifest_path = result.manifest_path.relative_to(project_dir)
    test_world_dir = Path("minecraft-test-world")
    fixture_summary_data = json.loads(result.location_result.draft_result.fixture_summary_path.read_text(encoding="utf-8"))
    fixture_starter_test = dict(fixture_summary_data.get("starterTest", {}))
    from titanforge.core.project_first_map import build_first_map_test_world_strategy
    from titanforge.core.project_first_map import build_first_map_focus_anchor_commands
    from titanforge.core.project_first_map import build_first_map_datapack_start
    from titanforge.core.project_first_map import build_first_map_route_handoffs
    from titanforge.core.project_first_map import build_first_map_story_walkthrough
    from titanforge.core.project_first_map import build_first_map_size_options
    from titanforge.core.project_first_map import build_first_map_recommended_manual_start
    test_world_strategy = build_first_map_test_world_strategy(
        result.template_result.config.width,
        result.template_result.config.length,
    )
    focus_anchor_commands = build_first_map_focus_anchor_commands(
        result.project_dir,
        result.template_result.config,
        int(test_world_strategy["recommendedMaxSide"]),
    )
    route_handoffs = build_first_map_route_handoffs(
        result.project_dir,
        result.template_result.config,
        int(test_world_strategy["recommendedMaxSide"]),
    )
    recommended_walkthrough = build_first_map_story_walkthrough(
        result.project_dir,
        result.template_result.config,
        int(test_world_strategy["recommendedMaxSide"]),
    )
    size_options = build_first_map_size_options(
        result.project_dir,
        result.template_result.config.width,
        result.template_result.config.length,
    )
    recommended_manual_start = build_first_map_recommended_manual_start(
        result.project_dir,
        recommended_max_side=int(test_world_strategy["recommendedMaxSide"]),
    )
    datapack_start = build_first_map_datapack_start(
        result.project_dir,
        datapack_zip_path=result.location_result.draft_result.datapack_fixture_zip_path,
        fixture_summary_path=result.location_result.draft_result.fixture_summary_path,
    )
    refresh_command = f'py -3.11 -m titanforge first-map-refresh "{result.project_dir.name}"'
    resize_command = (
        f'py -3.11 -m titanforge first-map-resize "{result.project_dir.name}" '
        "--width <blocks> --length <blocks>"
    )
    retheme_command = f'py -3.11 -m titanforge first-map-retheme "{result.project_dir.name}" --preset <preset-name>'
    set_story_command = (
        f'py -3.11 -m titanforge first-map-set-story "{result.project_dir.name}" '
        '--premise "<story text>" --player-feeling "<player feeling>"'
    )
    set_regions_command = (
        f'py -3.11 -m titanforge first-map-set-regions "{result.project_dir.name}" '
        '--region "<title>|<kind>|<story role>|<mood>|<coverage>"'
    )
    first_map_status_command = f'py -3.11 -m titanforge first-map-status "{result.project_dir.name}"'
    build_test_world_command = (
        f'py -3.11 -m titanforge first-map-test-world "{result.project_dir.name}" '
        f'--max-side {test_world_strategy["recommendedMaxSide"]}'
    )
    grow_test_world_command = f'py -3.11 -m titanforge first-map-test-world-grow "{result.project_dir.name}"'
    verify_test_world_command = (
        f'py -3.11 -m titanforge first-map-test-world-verify "{result.project_dir.name}" '
        "--check minecraft-open --check-status passed"
    )
    test_world_status_command = (
        f'py -3.11 -m titanforge first-map-test-world-status "{result.project_dir.name}" '
        f'--sample-dir "{test_world_dir.as_posix()}"'
    )
    focus_anchor_preview = "<br>".join(
        f'{escape(command)}<br><small>status: {escape(status_command)}</small>'
        for _, command, _, status_command in focus_anchor_commands[:4]
    )
    route_handoff_preview = "<br><br>".join(
        (
            f'<strong>{escape(route.route_id)} [{escape(route.kind)}]</strong>: {escape(route.summary)}<br>'
            f'<small>start:</small> {escape(route.start_command)}<br>'
            f'<small>status:</small> {escape(route.start_status_command)}<br>'
            f'<small>end:</small> {escape(route.end_command)}<br>'
            f'<small>status:</small> {escape(route.end_status_command)}'
        )
        for route in route_handoffs[:3]
    )
    walkthrough_preview = "<br><br>".join(
        (
            f'<strong>{escape(step.step_id)}: {escape(step.title)}</strong><br>'
            f'{escape(step.summary)}<br>'
            f'<small>shell:</small> {escape(step.command)}<br>'
            f'<small>status:</small> {escape(step.status_command)}'
        )
        for step in recommended_walkthrough
    )
    size_options_preview = "<br><br>".join(
        (
            f'<strong>{escape(option.label)}</strong>: {option.width} x {option.length} '
            f'[{escape(option.scale_label)}]<br>'
            f'{escape(option.summary)}<br>'
            f'<small>rerun:</small> {escape(option.rerun_command)}'
        )
        for option in size_options
    )
    warning_items = "\n".join(f"<li>{escape(warning)}</li>" for warning in result.location_result.warnings) or "<li>No workflow warnings for this pass.</li>"
    region_lineup = ", ".join(region.title for region in result.template_result.config.regions[:3])
    if len(result.template_result.config.regions) > 3:
        region_lineup = f"{region_lineup}, +{len(result.template_result.config.regions) - 3} more"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(result.template_result.config.name)} - TitanForge First Map</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #efe8dc;
      --panel: #fffaf2;
      --ink: #1e1913;
      --muted: #645c52;
      --line: #d8c8b2;
      --accent: #2c5a5a;
      --accent-soft: #dbeceb;
      --warn: #8f6700;
      --warn-soft: #f6e7bc;
      --shadow: rgba(36, 27, 18, 0.08);
      font-family: "Segoe UI", Tahoma, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.5), transparent 32%),
        linear-gradient(180deg, #eadcc5 0%, var(--bg) 48%, #efe7dc 100%);
    }}
    main {{
      width: min(1160px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }}
    .hero, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: 0 20px 40px var(--shadow);
      padding: 22px;
    }}
    .panel + .panel {{ margin-top: 20px; }}
    .eyebrow {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.88rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(2rem, 4vw, 3.2rem);
      line-height: 1.04;
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 1.25rem;
    }}
    .lead {{
      margin: 0;
      max-width: 820px;
      color: var(--muted);
      line-height: 1.6;
      font-size: 1.03rem;
    }}
    .stats, .links {{
      display: grid;
      gap: 16px;
    }}
    .stats {{
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin-top: 18px;
    }}
    .links {{
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }}
    .stat, .card {{
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
    }}
    .stat p, .card p, li {{
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
    }}
    .stat-label {{
      margin-bottom: 6px !important;
      font-size: 0.9rem;
    }}
    .stat-value {{
      color: var(--ink) !important;
      font-size: 1.35rem;
      font-weight: 700;
    }}
    .badge {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
      font-size: 0.84rem;
      margin-bottom: 12px;
    }}
    .warn-list {{
      background: var(--warn-soft);
      border: 1px solid #e2ca8d;
      border-radius: 18px;
      padding: 16px 18px;
    }}
    a {{
      color: var(--accent);
      font-weight: 700;
    }}
    code {{
      background: #f4ecdd;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 1px 5px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.93em;
    }}
    @media (max-width: 640px) {{
      main {{
        width: min(100% - 20px, 1160px);
        padding-top: 16px;
      }}
      .hero, .panel, .stat, .card {{
        padding: 14px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">TitanForge First Map</p>
      <h1>{escape(result.template_result.config.name)}</h1>
      <p class="lead">This is the root entry page for the one-command scenario-writer workflow. Start here, then branch into the location review, draft review, or Minecraft test artifacts only when the overview still feels right.</p>
      <div class="stats">
        <article class="stat">
          <p class="stat-label">World size</p>
          <p class="stat-value">{result.template_result.config.width} x {result.template_result.config.length}</p>
        </article>
        <article class="stat">
          <p class="stat-label">Preset</p>
          <p class="stat-value">{escape(result.template_result.preset_name)}</p>
        </article>
        <article class="stat">
          <p class="stat-label">Draft raster</p>
          <p class="stat-value">{result.location_result.draft_result.raster_width} x {result.location_result.draft_result.raster_length}</p>
        </article>
        <article class="stat">
          <p class="stat-label">Blocks per pixel</p>
          <p class="stat-value">{result.location_result.draft_result.blocks_per_pixel}</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>Quick Path</h2>
      <div class="links">
        <article class="card">
          <div class="badge">1</div>
          <h3>Set size first</h3>
          <p>If the world should be smaller or larger, run <code>{escape(resize_command)}</code>. Safe planning range stays <code>64 .. 32000</code> blocks per side.</p>
        </article>
        <article class="card">
          <div class="badge">2</div>
          <h3>Shape the story</h3>
          <p>Switch the starter theme with <code>{escape(retheme_command)}</code>, rewrite the premise with <code>{escape(set_story_command)}</code>, or replace the region lineup with <code>{escape(set_regions_command)}</code>.</p>
        </article>
        <article class="card">
          <div class="badge">3</div>
          <h3>Refresh and reread</h3>
          <p>After edits, rebuild with <code>{escape(refresh_command)}</code>. If you only need the current handoff again, run <code>{escape(first_map_status_command)}</code>.</p>
        </article>
        <article class="card">
          <div class="badge">4</div>
          <h3>Try one Minecraft sample</h3>
          <p>When the overview still feels right, run <code>{escape(build_test_world_command)}</code>, open <code>{escape(recommended_manual_start.checklist_path)}</code>, reread status with <code>{escape(test_world_status_command)}</code>, record the result with <code>{escape(verify_test_world_command)}</code>, and only then grow with <code>{escape(grow_test_world_command)}</code>.</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>How Size Works</h2>
      <div class="links">
        <article class="card">
          <h3>Logical world size</h3>
          <p><code>{result.template_result.config.width} x {result.template_result.config.length}</code> is the intended Minecraft footprint in blocks. Use <code>first-map-resize</code> when the story needs a bigger or smaller world without hand-editing the config.</p>
        </article>
        <article class="card">
          <h3>Draft raster</h3>
          <p><code>{result.location_result.draft_result.raster_width} x {result.location_result.draft_result.raster_length}</code> is the lighter planning preview, not the final block export. TitanForge keeps this smaller on purpose so very large worlds stay reviewable.</p>
        </article>
        <article class="card">
          <h3>Scale bridge</h3>
          <p><code>1 px = {result.location_result.draft_result.blocks_per_pixel} blocks</code>. Use this value when you compare the preview against the intended in-game size.</p>
        </article>
        <article class="card">
          <h3>World scale</h3>
          <p><strong>{escape(scale.label)}</strong>. {escape(scale.summary)} {escape(scale.planning_note)}</p>
        </article>
        <article class="card">
          <h3>Change size safely</h3>
          <p>Run <code>py -3.11 -m titanforge first-map-resize "{escape(result.project_dir.name)}" --width &lt;blocks&gt; --length &lt;blocks&gt;</code>. TitanForge accepts <code>64 .. 32000</code> blocks on each side. Starter examples:<br><code>{size_options_preview}</code></p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>Preset Intent</h2>
      <div class="links">
        <article class="card">
          <h3>Preset story</h3>
          <p>{escape(result.template_result.config.premise)}</p>
        </article>
        <article class="card">
          <h3>Player feeling</h3>
          <p>{escape(result.template_result.config.player_experience)}</p>
        </article>
        <article class="card">
          <h3>Key regions</h3>
          <p>{escape(region_lineup)}</p>
        </article>
        <article class="card">
          <h3>Switch starter theme</h3>
          <p>Run <code>py -3.11 -m titanforge first-map-retheme "{escape(result.project_dir.name)}" --preset &lt;preset-name&gt;</code> when you want another starter story and region lineup without hand-editing TOML.</p>
        </article>
        <article class="card">
          <h3>Change story text</h3>
          <p>Run <code>py -3.11 -m titanforge first-map-set-story "{escape(result.project_dir.name)}" --premise "&lt;story text&gt;" --player-feeling "&lt;player feeling&gt;"</code> when the scenario needs a different premise or player feeling without hand-editing TOML.</p>
        </article>
        <article class="card">
          <h3>Set custom regions</h3>
          <p>Run <code>py -3.11 -m titanforge first-map-set-regions "{escape(result.project_dir.name)}" --region "&lt;title&gt;|&lt;kind&gt;|&lt;story role&gt;|&lt;mood&gt;|&lt;coverage&gt;"</code> and repeat <code>--region</code> for every zone you want to keep.</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>Open These In Order</h2>
      <div class="links">
        <article class="card">
          <div class="badge">1</div>
          <h3><a href="{escape(location_review.as_posix())}">location/review.html</a></h3>
          <p>Open this first for the main non-technical review surface with previews, validation, fixture summary, and next Minecraft test commands.</p>
        </article>
        <article class="card">
          <div class="badge">2</div>
          <h3><a href="{escape(draft_review.as_posix())}">draft/review.html</a></h3>
          <p>Open this when you need the earlier planning view behind the location pack, especially for region balance and rough world shape.</p>
        </article>
        <article class="card">
          <div class="badge">3</div>
          <h3><a href="{escape(config_path.as_posix())}">titanforge.toml</a></h3>
          <p>Edit this when the world brief or story regions still need adjustment, then run <code>py -3.11 -m titanforge first-map-refresh "{escape(result.project_dir.name)}"</code> to rebuild the handoff.</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>Story Routes</h2>
      <div class="links">
        <article class="card">
          <h3><a href="{escape(route_preview.as_posix())}">route-preview.png</a></h3>
          <p>Use this when you want the shortest visual read of player movement and reveal lines between the named regions.</p>
        </article>
        <article class="card">
          <h3><a href="{escape(route_plan.as_posix())}">route-plan.json</a></h3>
          <p>Use this when you need the exact route ids and anchor pairs behind the preview.</p>
        </article>
        <article class="card">
          <h3>Recommended walkthrough</h3>
          <p>Use this when you want the shortest beginner-friendly path through the story world before opening every route pair:<br><code>{walkthrough_preview}</code></p>
        </article>
        <article class="card">
          <h3>Full route sample pairs</h3>
          <p>When the walkthrough is not enough, inspect the full route shell pairs from <code>first-map-status</code> or <code>first-map-manifest.json</code>. Typical pairs look like:<br><code>{route_handoff_preview}</code></p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>Minecraft Test Handoff</h2>
      <div class="links">
        <article class="card">
          <h3><a href="{escape(minecraft_first_pass.as_posix())}">minecraft-first-pass.txt</a></h3>
          <p>Open this first when you want one short world-side datapack checklist without reading the longer review blocks.</p>
        </article>
        <article class="card">
          <h3><a href="{escape(fixture_summary.as_posix())}">fixture-summary.json</a></h3>
          <p>Read this before using the datapack in a real world. It tells you footprint, fill-command count, and safety warnings.</p>
        </article>
        <article class="card">
          <h3><a href="{escape(fixture_commands.as_posix())}">fixture-commands.txt</a></h3>
          <p>Use this when you need the exact <code>/reload</code>, place, and clear commands.</p>
        </article>
        <article class="card">
          <h3><a href="{escape(datapack_zip.as_posix())}">datapack-fixture.zip</a></h3>
          <p>Use this only after the summary looks safe and the draft still matches the story you wanted.</p>
        </article>
        <article class="card">
          <h3>First in-world datapack pass</h3>
          <p>{escape(datapack_start.summary)} Starter verdict: <strong>{escape(str(fixture_starter_test.get("verdict", "unknown")))}</strong>.</p>
          <p>Copy <code>{escape(datapack_start.datapack_zip_path)}</code> into a throwaway world <code>datapacks</code> folder, then run <code>{escape(datapack_start.reload_command)}</code>, <code>{escape(datapack_start.place_command)}</code>, and later <code>{escape(datapack_start.clear_command)}</code>.</p>
        </article>
        <article class="card">
          <h3>Recommended first manual-open path</h3>
          <p>{escape(recommended_manual_start.summary)} Install the donor extra with <code>{escape(recommended_manual_start.install_extra_command)}</code>, then run <code>{escape(recommended_manual_start.build_command)}</code>.</p>
          <p>After it finishes, open <code>{escape(recommended_manual_start.checklist_path)}</code> first and later reread status with <code>{escape(recommended_manual_start.status_command)}</code>.</p>
        </article>
        <article class="card">
          <h3>Why this sample size</h3>
          <p>TitanForge recommends <code>--max-side {escape(str(test_world_strategy["recommendedMaxSide"]))}</code> here because {escape(str(test_world_strategy["reason"]))}</p>
        </article>
        <article class="card">
          <h3>Sample file scope</h3>
          <p>{escape(str(test_world_strategy["regionFileSummary"]))}</p>
          <p>{escape(str(test_world_strategy["multiRegionSummary"]))}</p>
        </article>
        <article class="card">
          <h3>Anchor-focused shell starts</h3>
          <p>When the first shell should target a specific reveal point instead of the region default, reuse the anchor commands from <code>first-map-status</code>. Typical starts look like:<br><code>{focus_anchor_preview}</code></p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>Workflow Warnings</h2>
      <div class="warn-list">
        <ul>
          {warning_items}
        </ul>
      </div>
    </section>

    <section class="panel">
      <h2>Raw Manifest</h2>
      <p><a href="{escape(manifest_path.as_posix())}">first-map-manifest.json</a> records the config path, review targets, and handoff artifacts for this run.</p>
    </section>
  </main>
</body>
</html>
"""
