# Night Runs

Night runs are for leaving the PC working without watching the screen.

They should run deterministic commands, write reports, and stop cleanly. They are not an excuse to let an AI chat edit code all night.

## Command

```powershell
$env:PYTHONPATH='src'
python -m titanforge night-run night_runs\first --count 200 --width 128 --height 128 --size-step 32 --max-minutes 480
```

## Outputs

Each run creates:

```text
night-run-summary.txt
night-run-manifest.json
case-0001-128x128\
case-0002-160x160\
case-0003-192x192\
...
```

Each case is a location pack with:

```text
mask.png
mask-preview.png
mask-cleanup-preview.png
layout.json
heightmap-preview.png
report.txt
manifest.json
```

## Why It Does Not Die After One Bad Case

`night-run` catches per-case generation failures, writes the failure into the manifest, and continues with the next case.

It also rewrites `night-run-summary.txt` and `night-run-manifest.json` after every completed case. If the PC sleeps or the process stops, the latest progress is still visible.

## Morning Review Prompt

Paste this into Codex:

```text
Check the latest TitanForge night run.
Folder: C:\Users\Li2Fox\Documents\ГИГАНТ\night_runs
Read the newest night-run-summary.txt and night-run-manifest.json.
Tell me:
1. what succeeded;
2. what failed;
3. which preview folders I should inspect first;
4. the next 3 options.
Keep it short.
```

## Rule

Use night runs to spend computer time, not model tokens.
