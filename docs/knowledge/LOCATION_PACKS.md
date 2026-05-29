# Location Packs

Location packs are the first tangible TitanForge output folder. They are not Minecraft worlds yet.

The goal is to collect all early artifacts needed to review a location idea:

```text
location/
  mask.png
  mask-preview.png
  layout.json
  heightmap-preview.png
  report.txt
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

## Validation

The pack writes `report.txt` and `manifest.json`.

Warnings do not stop the build. Errors return a non-zero CLI exit code.

Current warnings include:

- unknown mask colors
- missing water
- missing land
- mostly water
- mostly land

## Product Meaning

This is the first useful "touch it" version of TitanForge:

```text
PNG mask or generated demo
-> visible mask preview
-> neutral layout JSON
-> heightmap preview
-> validation report
```

Minecraft export comes later. Location packs keep early work inspectable before expensive terrain and exporter passes exist.
