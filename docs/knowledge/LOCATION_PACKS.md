# Location Packs

Location packs are the first tangible TitanForge output folder. They are not Minecraft worlds yet.

The goal is to collect all early artifacts needed to review a location idea:

```text
location/
  mask.png
  mask-preview.png
  mask-cleanup-preview.png
  coastline-smoothing-preview.png
  layout.json
  terrain-color-preview.png
  heightmap-preview.png
  report.txt
  review.html
  manifest.json
```

## Build From Demo Input

```powershell
$env:PYTHONPATH = "src"
python -m titanforge build-location out\demo-location --width 128 --height 128
```

No `--input` means demo mode. This is useful for smoke testing.

## Build From User Mask

```powershell
$env:PYTHONPATH = "src"
python -m titanforge build-location out\my-location --input path\to\mask.png
```

The input mask is copied into the pack as `mask.png`.

## Cleanup As Terrain Input

By default, `heightmap-preview.png` is rendered from the original `mask.png`.

Use this when you want tiny water/land specks cleaned before terrain preview:

```powershell
python -m titanforge build-location out\my-location --input path\to\mask.png --use-cleanup-for-heightmap
```

The original mask and report still remain in the pack. The manifest records which mask was used for heightmap generation:

```json
{
  "terrain": {
    "cleanupApplied": true,
    "heightmapSource": "mask-cleanup-preview.png"
  }
}
```

## Validation

The pack writes `report.txt` and `manifest.json`.

`report.txt` is meant to be readable without opening JSON first. It includes:

- the technical validation status;
- a short human summary of the location;
- plain-language review notes for warnings and errors.

Warnings do not stop the build. Errors return a non-zero CLI exit code.

Current warnings include:

- unknown mask colors
- missing water
- missing land
- mostly water
- mostly land

`mask-cleanup-preview.png` is included to reveal tiny water/land noise before terrain generation.

`coastline-smoothing-preview.png` is a separate diagnostic pass that softens stair-step coast edges. It is meant for human review, not as a silent replacement for the source mask.

`terrain-color-preview.png` is the first readable terrain surface draft. It lets a human distinguish water, beach, forest, city, roads, ports, land, and mountains before relying on grayscale heightmaps.

`mask-cleanup-preview.png` can optionally be used for `terrain-color-preview.png` and `heightmap-preview.png`, but it does not replace `mask.png`.

`review.html` is a static local review page for the pack. Open it in a browser to inspect the five preview images, validation status, raw file links, and the full text report without building a GUI or starting a server.

## Product Meaning

This is the first useful "touch it" version of TitanForge:

```text
PNG mask or generated demo
-> visible mask preview
-> coastline smoothing preview
-> terrain color preview
-> neutral layout JSON
-> heightmap preview
-> validation report
-> static review page
```

Minecraft export comes later. Location packs keep early work inspectable before expensive terrain and exporter passes exist.
