# Start Here

This is the short handoff for humans and new Codex/GPT chats.

## What This Is

TitanForge Engine is an external toolkit for generating cinematic Minecraft map/location artifacts.

Current state:

- works as a Python CLI prototype;
- can build a first project draft pack from `titanforge.toml`;
- can bridge `titanforge.toml` directly into a draft plus location pack;
- shapes draft regions more like coast / forest / settlement / ridge instead of only straight strips;
- writes story anchors into `world-plan.json` for later placement and routing passes;
- writes first deterministic transition artifacts between neighboring regions;
- writes a first Minecraft 1.21.11 material profile from neutral planning artifacts;
- writes a first Minecraft 1.21.11 export request from neutral planning artifacts;
- writes a first Minecraft 1.21.11 chunk plan from neutral planning artifacts;
- writes a first Minecraft 1.21.11 block fixture from neutral planning artifacts;
- writes a first Minecraft 1.21.11 NBT-oriented fixture from neutral planning artifacts;
- writes a first Minecraft 1.21.11 mcfunction fixture from neutral planning artifacts;
- writes a first Minecraft 1.21.11 clear-fixture mcfunction companion from neutral planning artifacts;
- writes a first fixture-commands guide with exact place and clear function calls plus unsupported-target warnings;
- writes a first fixture-summary artifact with rough bounds, fill-command counts, and safety warnings;
- writes a first Minecraft 1.21.11 datapack fixture package from neutral planning artifacts;
- writes a first zipped Minecraft 1.21.11 datapack fixture package from neutral planning artifacts;
- explains the key draft artifacts directly inside the world brief review page;
- writes first deterministic route artifacts from those anchors;
- writes first deterministic placement artifacts from anchors and routes;
- writes first deterministic road artifacts from routes and placement sites;
- writes first deterministic settlement blockout artifacts from placement sites and roads;
- creates PNG masks, terrain previews, layout JSON, reports, and location-pack folders;
- warns when draft scale is too compressed to trust small details;
- warns when a large world brief is too sparse or lacks enough zone contrast;
- has a resilient `night-run` command for unattended batch generation;
- does not yet export playable Minecraft worlds or schematics.

Do not sell it as finished. Treat it as a stable early pipeline.

## What To Run First

```powershell
git status --short --branch
git pull origin main
$env:PYTHONPATH='src'
python -m unittest discover -s tests
python -m compileall -q src tests
```

Windows note:

- if `python --version` prints only `Python` or launches the Microsoft Store alias, use `py -3.11` instead of `python`;
- run `unittest` and `compileall` sequentially, not in parallel, or Windows may throw false `__pycache__` permission errors.

If tests pass, run a small smoke:

```powershell
$env:PYTHONPATH='src'
py -3.11 -m titanforge project-location examples\tiny_project\titanforge.toml previews\tiny-project-location --max-draft-side 256 --use-cleanup-for-heightmap
```

If you want the fastest scenario-writer flow instead of the example project, use:

```powershell
$env:PYTHONPATH='src'
py -3.11 -m titanforge first-map previews\my-first-world --name "My First World" --width 2048 --length 1536 --preset coastal-valley --max-draft-side 256
```

If you are unsure which starter world to pick, inspect them first:

```powershell
$env:PYTHONPATH='src'
py -3.11 -m titanforge preset-catalog
```

If a future UI or helper script needs the same preset list as structured data:

```powershell
$env:PYTHONPATH='src'
py -3.11 -m titanforge preset-catalog --json
```

Then open:

```text
previews\my-first-world\review.html
```

That root page explains one important thing up front: it shows what story the preset is aiming for, which regions anchor it, `width` and `length` are the intended Minecraft world size in blocks, it labels that size in plain language, and the draft preview can stay smaller while reporting its `blocksPerPixel` scale. It now also shows a few exact starter size examples and rerun commands, so changing from a small test map to a very large cinematic world does not require guessing. The same guidance plus a machine-readable open order, command hints, and Minecraft handoff artifact order is also mirrored into `first-map-manifest.json` for later UI automation.

If you come back to that folder later and only need the current handoff again, do not rebuild it. Run:

```powershell
$env:PYTHONPATH='src'
py -3.11 -m titanforge first-map-status previews\my-first-world
```

That terminal status is now meant to stand on its own: it repeats the preset intent, size guidance, review order, next change actions, and Minecraft-side cautions from `first-map-manifest.json`, not just raw file paths. It now starts with a short recommended walkthrough built from the current route plan, explains whether the starter sample stays in one `.mca` file or later grows into several sampled region files, then keeps the fuller route-focused, region-focused, and anchor-focused sample commands available below when you need deeper inspection.

The Minecraft handoff now also surfaces a plain starter-test verdict from `fixture-summary.json` such as `safe` or `caution`, and it now starts with one recommended first manual-open path plus a sampled `.mca` file-scope note, so you can begin with the safest disposable sample before looking at the deeper focused options.

If you want the shortest current path from that `first-map` folder to one experimental Minecraft manual-open candidate, install the optional donor extra and run:

```powershell
py -3.11 -m pip install -e .[donor-spikes]
$env:PYTHONPATH='src'
py -3.11 -m titanforge first-map-test-world previews\my-first-world
```

That writes `previews\my-first-world\minecraft-test-world`. If you omit `--max-side`, TitanForge chooses a safer first sampled window from the logical world size and also repeats that recommendation in `first-map-status`. Add `--focus-region "Harbor Town"` or another region title from `first-map-status` when you want the sampled shell to recenter around a specific story zone. Add `--focus-anchor "arrival"` together with that region when you want the shell aimed at one exact anchor inside the chosen region. Focused runs now default to their own sibling folders like `minecraft-test-world-harbor-town` or `minecraft-test-world-broken-ridge-ridge-vista`, so you can compare multiple samples without overwriting the base shell. Larger manual samples can now span several sampled `.mca` files when needed, while the default starter sample stays smaller and safer. Open `verification-checklist.txt` first, then use `py -3.11 -m titanforge anvil-test-world-status previews\my-first-world\minecraft-test-world` when you need the current manual-test status again. That status now also tells you the sampled source origin, the focused region/anchor, the next sampled window to try after a passed manual check, or to go back to `first-map-status` first if the sample failed.

If you need a fresh world brief instead of the example file, start here:

```powershell
$env:PYTHONPATH='src'
py -3.11 -m titanforge init-project previews\my-first-world --name "My First World" --width 2048 --length 1536 --preset coastal-valley
```

Then the current location-pack smoke:

```powershell
$env:PYTHONPATH='src'
python -m titanforge build-location previews\demo-location --width 128 --height 128 --use-cleanup-for-heightmap
```

If you explicitly need the current donor-backed `.mca` lab spike, install the optional extra first:

```powershell
py -3.11 -m pip install -e .[donor-spikes]
py -3.11 -m titanforge anvil-region-spike examples\tiny_project\titanforge.toml previews\tiny-anvil-spike --max-side 128
py -3.11 -m titanforge anvil-save-shell examples\tiny_project\titanforge.toml previews\tiny-save-shell --max-side 128
py -3.11 -m titanforge anvil-test-world examples\tiny_project\titanforge.toml previews\tiny-test-world --max-side 128
```

These are narrow donor-backed experiments, not a full world export. `anvil-save-shell` is the safer inspection handoff, while `anvil-test-world` is the first manual-open candidate because it also writes `level.dat` and `session.lock`. The sampled `region\` folder can now contain more than one `r.<x>.<z>.mca` file when you request a larger bounded sample. That test-world output now also includes `verification-checklist.txt` and `verification-report.json`; open the checklist first, then record the result in the report. Use `--focus-region "<Region Title>"` when you want the donor-backed sample to target one named region from `titanforge.toml` instead of the world origin. Use `--focus-anchor "<Anchor Id>"` together with that region when you want the sample to start from one explicit anchor inside it. Use `anvil-test-world-verify` to update the report instead of editing JSON by hand, and `anvil-test-world-status` to read the current status later without rebuilding the folder. The status command now also shows each individual check state, the sampled source origin, the focused region/anchor, and highlights failed checks in one compact line.

## Overnight Work

Use this when the PC should work without supervision:

```powershell
$env:PYTHONPATH='src'
python -m titanforge night-run night_runs\first --count 200 --width 128 --height 128 --size-step 32 --max-minutes 480
```

If the Windows `python` alias is broken, use:

```powershell
$env:PYTHONPATH='src'
py -3.11 -m titanforge night-run night_runs\first --count 200 --width 128 --height 128 --size-step 32 --max-minutes 480
```

Morning review:

```text
Check the latest TitanForge night run.
Folder: C:\Users\Li2Fox\Documents\ГИГАНТ\night_runs
Read the newest night-run-summary.txt and night-run-manifest.json.
Tell me what succeeded, what failed, which preview folders to inspect first, and the next 3 options.
Keep it short.
```

## Prompt For A New Codex Chat

Paste this:

```text
Continue TitanForge Engine.
Repository: https://github.com/mio-openliven/titanforge-engine
Working folder if local: C:\Users\Li2Fox\Documents\ГИГАНТ

Read START_HERE.md, README.md, AGENTS.md, tasks.md, and docs/operations/NIGHT_RUNS.md.
Run:
git status --short --branch
git pull origin main
$env:PYTHONPATH='src'
python -m unittest discover -s tests
python -m compileall -q src tests

If `python` is a broken Windows Store alias, use `py -3.11` for the same commands.
Run the test and compile commands sequentially, not in parallel.

I am a beginner in code. Keep answers short and practical.
Pick one safe next task only.
Do not start GUI or Minecraft export unless the current CLI/preview pipeline is verified.
If I write "+" or "continue", choose the safest useful next step yourself.
After a verified change, update docs/tasks and commit/push to main.
```

## What Not To Do

- Do not rewrite the whole project.
- Do not mix GUI, AI prompts, terrain, exporters, and asset library in one pass.
- Do not import donor code before license review.
- Do not leave AI coding overnight without human review.
- Do not commit generated `night_runs/`, `out/`, or preview output folders.

## Current Best Next Steps

1. Design the first Minecraft 1.21.11 export adapter from neutral artifacts.
2. Move from simple shape hints to multi-region composition rules between anchors.
3. Turn the datapack fixture into the first tiny Minecraft-consumable structure workflow.
4. Deepen transition/composition rules between neighboring regions instead of only seam bands.
5. Only after that, begin larger exporter experiments.
