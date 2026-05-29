# Decisions

## 2026-05-29: Product Identity

TitanForge Engine is an external procedural toolkit and generation engine for cinematic Minecraft maps.

It should not be described as a game, mod, or plugin.

Version priorities:

- Primary product target: Minecraft 1.21.11
- Secondary compatibility target: Minecraft 1.12.2

The product should prioritize our own long-term direction. A YouTuber/client target can justify compatibility work, but should not become the architectural center because that relationship may not be reliable.

Implementation bias: build from a neutral internal representation toward version-specific exporters. Prefer modern-first design with a downgrade adapter for 1.12.2 where feasible.

## 2026-05-29: Naming

Use `TitanForge Engine` as the display name.

Use `titanforge-engine` as the repository and package-style slug.

## 2026-05-29: Git and Assets

Use GitHub private repository with Git LFS enabled for heavy binary assets such as schematics, region files, images, videos, archives, and 3D files.

## 2026-05-29: Knowledge Base

Project memory should live in repo docs instead of relying only on chat history.
