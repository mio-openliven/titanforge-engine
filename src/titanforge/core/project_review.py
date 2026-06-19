from __future__ import annotations

from html import escape
from pathlib import Path

from titanforge.core.project import ProjectConfig, ProjectRegion


def write_project_review_page(config: ProjectConfig, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = _format_project_review_html(config)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _format_project_review_html(config: ProjectConfig) -> str:
    region_cards = "\n".join(_format_region_card(region) for region in config.regions) or """
      <article class="card muted-card">
        <h3>No regions yet</h3>
        <p>Add <code>[[regions]]</code> blocks to the project file so this world starts feeling like a real place.</p>
      </article>
    """

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(config.name)} - TitanForge World Brief</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #efe6d6;
      --panel: #fffaf2;
      --ink: #201912;
      --muted: #675d52;
      --line: #d8c6ab;
      --accent: #234f69;
      --accent-soft: #dcecf4;
      --shadow: rgba(37, 26, 15, 0.08);
      font-family: "Segoe UI", Tahoma, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(255,255,255,0.5), transparent 32%),
        linear-gradient(180deg, #ece0cb 0%, var(--bg) 48%, #efe7da 100%);
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
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
    .stats, .regions {{
      display: grid;
      gap: 16px;
    }}
    .stats {{
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin-top: 18px;
    }}
    .regions {{
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
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
    .muted-card {{
      border-style: dashed;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    code {{
      background: #f4ecdd;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 1px 5px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.93em;
    }}
    .hint {{
      margin-top: 12px;
      color: var(--muted);
    }}
    @media (max-width: 640px) {{
      main {{
        width: min(100% - 20px, 1180px);
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
      <p class="eyebrow">TitanForge World Brief</p>
      <h1>{escape(config.name)}</h1>
      <p class="lead">{escape(config.premise)}</p>
      <div class="stats">
        <article class="stat">
          <p class="stat-label">World size</p>
          <p class="stat-value">{config.width} x {config.length}</p>
        </article>
        <article class="stat">
          <p class="stat-label">Planning range</p>
          <p class="stat-value">64 .. 32000</p>
        </article>
        <article class="stat">
          <p class="stat-label">Target version</p>
          <p class="stat-value">{escape(config.target_version)}</p>
        </article>
        <article class="stat">
          <p class="stat-label">Player feeling</p>
          <p class="stat-value">{escape(config.player_experience)}</p>
        </article>
      </div>
      <p class="hint">This page is the first human-facing planning surface. It describes the world you want before TitanForge tries to generate terrain or export Minecraft data.</p>
    </section>

    <section class="panel">
      <h2>How To Use This</h2>
      <ul>
        <li>Edit <code>titanforge.toml</code> with the world size, premise, and region list.</li>
        <li>Open this page to review whether the world concept already feels like a place with a story.</li>
        <li>Run <code>py -3.11 -m titanforge project-draft path\to\titanforge.toml out\my-world</code> to get the first draft pack.</li>
        <li>Large worlds are scaled into a smaller draft mask on purpose, so planning stays readable before later terrain and export passes.</li>
      </ul>
    </section>

    <section class="panel">
      <h2>What To Open After Project-Draft</h2>
      <div class="regions">
        <article class="card">
          <h3><code>review.html</code></h3>
          <p>Open this first to keep the world brief and the generated draft in the same mental frame.</p>
        </article>
        <article class="card">
          <h3><code>draft-mask.png</code></h3>
          <p>Check whether the world silhouette already reads like sea, city, forest, ridge, and village instead of noise.</p>
        </article>
        <article class="card">
          <h3><code>fixture-summary.json</code></h3>
          <p>Read this before Minecraft testing. It tells you rough footprint, fill-command count, and any safety warnings for the first fixture run.</p>
        </article>
        <article class="card">
          <h3><code>fixture-commands.txt</code></h3>
          <p>Use this when you need the exact <code>/reload</code>, place, or clear commands without reading mcfunction internals.</p>
        </article>
        <article class="card">
          <h3><code>datapack-fixture.zip</code></h3>
          <p>This is the easiest handoff artifact for a first world test. Drop it into a world datapacks folder only after the summary looks safe.</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>Story Regions</h2>
      <div class="regions">
        {region_cards}
      </div>
    </section>

    <section class="panel">
      <h2>Current Engine Reality</h2>
      <ul>
        <li>TitanForge can already plan and preview a location pack.</li>
        <li>It does not yet generate a full playable Minecraft world from this brief.</li>
        <li>This brief exists so ideas like city + sea + forest + mountains + village become explicit before generation logic grows.</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""


def _format_region_card(region: ProjectRegion) -> str:
    return f"""
      <article class="card">
        <div class="badge">{escape(region.kind)}</div>
        <h3>{escape(region.title)}</h3>
        <p><strong>Story role:</strong> {escape(region.story_role)}</p>
        <p><strong>Mood:</strong> {escape(region.mood)}</p>
        <p><strong>Coverage hint:</strong> {escape(region.coverage_hint)}</p>
        <p><strong>Notes:</strong> {escape(region.notes)}</p>
      </article>
    """
