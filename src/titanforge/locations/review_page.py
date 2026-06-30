from __future__ import annotations

from html import escape
from pathlib import Path


def write_location_review_page(
    output_dir: Path,
    *,
    pack_name: str,
    source_mode: str,
    validation_errors: int,
    validation_warnings: int,
    cleanup_applied: bool,
    heightmap_source: str,
    report_text: str,
    draft_artifacts: tuple[tuple[str, str], ...] = (),
    draft_fixture_summary: dict[str, object] | None = None,
    draft_fixture_commands: tuple[str, ...] = (),
) -> Path:
    review_page_path = output_dir / "review.html"
    status = "ERROR" if validation_errors else "OK"
    cleanup_text = "yes" if cleanup_applied else "no"
    draft_links_html = ""
    if draft_artifacts:
        draft_link_items = "\n".join(
            f'            <li><a href="{escape(path)}">{escape(label)}</a></li>' for label, path in draft_artifacts
        )
        draft_links_html = f"""
    <section class="panel">
      <h2>Project-Draft Links</h2>
      <p>Open these first when this location pack came from <code>project-location</code> and you need the draft-side planning context.</p>
      <div class="raw-grid">
        <div>
          <ul>
{draft_link_items}
          </ul>
        </div>
      </div>
    </section>
"""
    draft_summary_html = ""
    if draft_fixture_summary is not None:
        counts = draft_fixture_summary["counts"]
        bounds = draft_fixture_summary["bounds"]
        starter_test = draft_fixture_summary["starterTest"]
        warnings = draft_fixture_summary["warnings"]
        warning_items = ""
        if warnings:
            warning_items = "\n".join(f"            <li>{escape(str(warning))}</li>" for warning in warnings)
            warning_items = f"""
      <div>
        <h3>Fixture Warnings</h3>
        <ul>
{warning_items}
        </ul>
      </div>
"""
        draft_summary_html = f"""
    <section class="panel">
      <h2>Draft Fixture Summary</h2>
      <p>Use this before the first Minecraft test so command load and footprint are visible without opening JSON by hand.</p>
      <div class="summary-grid">
        <div class="metric">
          <p class="metric-label">Place fill commands</p>
          <p class="metric-value">{escape(str(counts["placeFillCommands"]))}</p>
        </div>
        <div class="metric">
          <p class="metric-label">Fixture cuboids</p>
          <p class="metric-value">{escape(str(counts["cuboids"]))}</p>
        </div>
        <div class="metric">
          <p class="metric-label">Fixture footprint</p>
          <p class="metric-value">{escape(str(bounds["width"]))} x {escape(str(bounds["length"]))} x {escape(str(bounds["height"]))}</p>
        </div>
      </div>
      <div>
        <h3>Starter Test Verdict</h3>
        <p><strong>{escape(str(starter_test["verdict"]))}</strong> · {escape(str(starter_test["summary"]))}</p>
        <p>{escape(str(starter_test["worldAdvice"]))}</p>
      </div>
{warning_items}
    </section>
"""
    draft_commands_html = ""
    if draft_fixture_commands:
        draft_commands_html = f"""
    <section class="panel">
      <h2>Next Minecraft Test</h2>
      <p>Use this exact command guide when you move from review artifacts into a first in-world datapack test.</p>
      <pre>{escape(chr(10).join(draft_fixture_commands))}</pre>
    </section>
"""

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(pack_name)} - TitanForge Review</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4efe5;
      --panel: #fffaf1;
      --ink: #1f1c17;
      --muted: #6a6258;
      --line: #dbcdb7;
      --accent: #245c43;
      --accent-soft: #d9eadf;
      --warn: #9f6a00;
      --warn-soft: #f7e7bf;
      --error: #9c2f2f;
      --error-soft: #f6d8d8;
      --shadow: rgba(32, 26, 18, 0.08);
      font-family: "Segoe UI", Tahoma, sans-serif;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.55), transparent 35%),
        linear-gradient(180deg, #efe3cc 0%, var(--bg) 45%, #efe7d8 100%);
      color: var(--ink);
    }}

    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }}

    .hero,
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: 0 18px 40px var(--shadow);
    }}

    .hero {{
      padding: 24px;
      margin-bottom: 20px;
    }}

    .eyebrow {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.9rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    h1 {{
      margin: 0 0 12px;
      font-size: clamp(1.9rem, 4vw, 3rem);
      line-height: 1.05;
    }}

    .status {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 16px;
      padding: 8px 12px;
      border-radius: 999px;
      font-weight: 700;
    }}

    .status-ok {{
      background: var(--accent-soft);
      color: var(--accent);
    }}

    .status-error {{
      background: var(--error-soft);
      color: var(--error);
    }}

    .summary-grid,
    .preview-grid,
    .raw-grid {{
      display: grid;
      gap: 16px;
    }}

    .summary-grid {{
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }}

    .preview-grid {{
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      margin: 20px 0;
    }}

    .raw-grid {{
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}

    .metric,
    .card,
    .panel {{
      padding: 18px;
    }}

    .metric {{
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid var(--line);
      border-radius: 16px;
    }}

    .metric-label {{
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 0.9rem;
    }}

    .metric-value {{
      margin: 0;
      font-size: 1.35rem;
      font-weight: 700;
    }}

    .card {{
      background: rgba(255, 255, 255, 0.74);
      border: 1px solid var(--line);
      border-radius: 18px;
    }}

    .card h2,
    .panel h2 {{
      margin: 0 0 12px;
      font-size: 1.1rem;
    }}

    img {{
      display: block;
      width: 100%;
      height: auto;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: #f8f4ec;
    }}

    p,
    li {{
      color: var(--muted);
      line-height: 1.5;
    }}

    .panel + .panel {{
      margin-top: 20px;
    }}

    pre {{
      margin: 0;
      padding: 16px;
      overflow-x: auto;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: #f7f1e6;
      color: var(--ink);
      white-space: pre-wrap;
      word-break: break-word;
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.94rem;
      line-height: 1.45;
    }}

    ul {{
      margin: 0;
      padding-left: 18px;
    }}

    a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    @media (max-width: 640px) {{
      main {{
        width: min(100% - 20px, 1120px);
        padding-top: 16px;
      }}

      .hero,
      .panel,
      .card,
      .metric {{
        padding: 14px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">TitanForge Location Pack Review</p>
      <h1>{escape(pack_name)}</h1>
      <p class="status {'status-error' if validation_errors else 'status-ok'}">{escape(status)} · {validation_errors} error(s) · {validation_warnings} warning(s)</p>
      <div class="summary-grid">
        <div class="metric">
          <p class="metric-label">Source mode</p>
          <p class="metric-value">{escape(source_mode)}</p>
        </div>
        <div class="metric">
          <p class="metric-label">Cleanup for heightmap</p>
          <p class="metric-value">{escape(cleanup_text)}</p>
        </div>
        <div class="metric">
          <p class="metric-label">Heightmap source</p>
          <p class="metric-value">{escape(heightmap_source)}</p>
        </div>
      </div>
    </section>

    <section class="preview-grid">
      <article class="card">
        <h2>Mask Preview</h2>
        <img src="mask-preview.png" alt="Mask preview">
        <p>Normalized zone colors from the source mask.</p>
      </article>
      <article class="card">
        <h2>Cleanup Preview</h2>
        <img src="mask-cleanup-preview.png" alt="Mask cleanup preview">
        <p>Tiny water and land noise removed for inspection.</p>
      </article>
      <article class="card">
        <h2>Coastline Smoothing Preview</h2>
        <img src="coastline-smoothing-preview.png" alt="Coastline smoothing preview">
        <p>Diagnostic pass that softens stair-step coast edges without touching the source mask.</p>
      </article>
      <article class="card">
        <h2>Terrain Color Preview</h2>
        <img src="terrain-color-preview.png" alt="Terrain color preview">
        <p>First readable terrain surface draft before block-level export.</p>
      </article>
      <article class="card">
        <h2>Heightmap Preview</h2>
        <img src="heightmap-preview.png" alt="Heightmap preview">
        <p>First grayscale terrain draft based on the current terrain source.</p>
      </article>
    </section>

    <section class="panel">
      <h2>Raw Files</h2>
      <div class="raw-grid">
        <div>
          <ul>
            <li><a href="mask.png">mask.png</a></li>
            <li><a href="mask-preview.png">mask-preview.png</a></li>
            <li><a href="mask-cleanup-preview.png">mask-cleanup-preview.png</a></li>
            <li><a href="coastline-smoothing-preview.png">coastline-smoothing-preview.png</a></li>
            <li><a href="terrain-color-preview.png">terrain-color-preview.png</a></li>
          </ul>
        </div>
        <div>
          <ul>
            <li><a href="layout.json">layout.json</a></li>
            <li><a href="manifest.json">manifest.json</a></li>
            <li><a href="report.txt">report.txt</a></li>
          </ul>
        </div>
      </div>
    </section>
{draft_links_html}
{draft_summary_html}
{draft_commands_html}

    <section class="panel">
      <h2>Validation Report</h2>
      <pre>{escape(report_text.strip())}</pre>
    </section>
  </main>
</body>
</html>
"""

    review_page_path.write_text(html, encoding="utf-8")
    return review_page_path
