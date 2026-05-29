# TitanForge Engine

TitanForge Engine is a procedural toolkit for generating cinematic Minecraft maps.

It is not a game or a Minecraft mod. It is an external development tool and engine for map generation workflows: masks, layouts, previews, terrain passes, schematics, and modular exporters.

Version priorities:

- Primary product target: Minecraft 1.21.11
- Secondary compatibility target: Minecraft 1.12.2

Project knowledge starts in [docs/knowledge/PROJECT_MAP.md](docs/knowledge/PROJECT_MAP.md).

## Local Smoke Test

```powershell
$env:PYTHONPATH = "src"
python -m titanforge info
python -m titanforge plan examples/tiny_project/titanforge.toml
python -m titanforge inventory examples
python -m titanforge demo-mask out\demo-mask.png
python -m titanforge mask-info path\to\mask.png
python -m titanforge mask-preview path\to\mask.png out\mask-preview.png
python -m titanforge mask-layout path\to\mask.png out\layout.json
python -m titanforge heightmap-preview out\layout.json out\heightmap-preview.png
python -m unittest discover -s tests
```

## Tiny Mask Pipeline

```powershell
$env:PYTHONPATH = "src"
python -m titanforge demo-mask out\demo-mask.png --width 128 --height 128
python -m titanforge mask-preview out\demo-mask.png out\demo-preview.png
python -m titanforge mask-layout out\demo-mask.png out\demo-layout.json
python -m titanforge heightmap-preview out\demo-layout.json out\demo-heightmap.png
```
