from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionTarget:
    minecraft_version: str
    tier: str
    role: str


PRIMARY_TARGET = VersionTarget(
    minecraft_version="1.21.11",
    tier="P0",
    role="primary product target",
)

ACTIVE_TARGETS = (
    PRIMARY_TARGET,
    VersionTarget(
        minecraft_version="1.20.1",
        tier="P1",
        role="modern ecosystem fallback candidate",
    ),
    VersionTarget(
        minecraft_version="1.12.2",
        tier="P1",
        role="legacy/client downgrade target",
    ),
)

PARKING_LOT_TARGETS = (
    VersionTarget(
        minecraft_version="1.19.2",
        tier="parking-lot",
        role="deferred compatibility candidate",
    ),
    VersionTarget(
        minecraft_version="1.18.2",
        tier="parking-lot",
        role="deferred worldgen-era candidate",
    ),
    VersionTarget(
        minecraft_version="1.16.5",
        tier="parking-lot",
        role="deferred legacy-modern bridge",
    ),
)
