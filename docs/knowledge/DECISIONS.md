# Decisions

## 2026-05-29: Product Identity

TitanForge Engine is an external procedural toolkit and generation engine for cinematic Minecraft maps.

It should not be described as a game, mod, or plugin.

Version priorities:

- Primary product target: Minecraft 1.21.11
- Secondary compatibility target: Minecraft 1.12.2

The product should prioritize our own long-term direction. A YouTuber/client target can justify compatibility work, but should not become the architectural center because that relationship may not be reliable.

Implementation bias: build from a neutral internal representation toward version-specific exporters. Prefer modern-first design with a downgrade adapter for 1.12.2 where feasible.

Popular versions inside the supported planning range should be represented as candidate adapters, not hard requirements.

Active version focus:

- 1.21.11: primary product target.
- 1.20.1: modern ecosystem fallback candidate.
- 1.12.2: legacy/client downgrade target.

Parking lot versions such as 1.19.2, 1.18.2, and 1.16.5 should not affect early architecture unless a real donor, library, or workflow requires them.

## 2026-05-29: Naming

Use `TitanForge Engine` as the display name.

Use `titanforge-engine` as the repository and package-style slug.

## 2026-05-29: Git and Assets

Use GitHub private repository with Git LFS enabled for heavy binary assets such as schematics, region files, images, videos, archives, and 3D files.

## 2026-05-29: Knowledge Base

Project memory should live in repo docs instead of relying only on chat history.
