from __future__ import annotations

from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, ZoneDefinition


class MaskColorClassifier:
    def __init__(self, palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE) -> None:
        self._zone_by_rgba = {zone.color.rgba: zone for zone in palette}
        self._zone_by_rgb = {zone.color.rgb: zone for zone in palette if zone.color.alpha == 255}
        self._void_zone = next((zone for zone in palette if zone.zone_id == "void"), None)

    def classify(self, rgba: tuple[int, int, int, int]) -> ZoneDefinition | None:
        zone = self._zone_by_rgba.get(rgba)
        if zone is not None:
            return zone

        if rgba[3] == 0:
            return self._void_zone

        if rgba[3] == 255:
            return self._zone_by_rgb.get(rgba[:3])

        return None
