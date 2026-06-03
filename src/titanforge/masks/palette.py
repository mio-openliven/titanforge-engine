from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaskColor:
    red: int
    green: int
    blue: int
    alpha: int = 255

    @classmethod
    def from_rgba(cls, rgba: tuple[int, int, int, int]) -> MaskColor:
        return cls(*rgba)

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    @property
    def rgba(self) -> tuple[int, int, int, int]:
        return (self.red, self.green, self.blue, self.alpha)

    @property
    def hex_rgb(self) -> str:
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"


@dataclass(frozen=True)
class ZoneDefinition:
    zone_id: str
    label: str
    color: MaskColor


DEFAULT_ZONE_PALETTE = (
    ZoneDefinition("water", "Water", MaskColor(0, 102, 255)),
    ZoneDefinition("land", "Land", MaskColor(59, 170, 53)),
    ZoneDefinition("mountain", "Mountain", MaskColor(119, 119, 119)),
    ZoneDefinition("beach", "Beach", MaskColor(194, 178, 128)),
    ZoneDefinition("road", "Road", MaskColor(64, 64, 64)),
    ZoneDefinition("forest", "Forest", MaskColor(31, 122, 31)),
    ZoneDefinition("city", "City", MaskColor(180, 74, 74)),
    ZoneDefinition("port", "Port", MaskColor(214, 154, 45)),
    ZoneDefinition("void", "Ignored / transparent", MaskColor(0, 0, 0, 0)),
)
