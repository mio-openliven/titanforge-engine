# Risks

## Technical Risks

- Minecraft 1.12.2 formats can be awkward and version-sensitive.
- Large binary assets can make Git painful without strict LFS discipline.
- A single giant script will become unmaintainable quickly.
- Preview rendering can drift from actual Minecraft output.
- Donor code licenses may restrict reuse.

## Process Risks

- Too many donors can create research paralysis.
- Importing the entire old project at once can bury the useful parts.
- Chat-only decisions can be lost.

## Mitigations

- Keep a small donor set first.
- Use tiny fixtures and examples before huge maps.
- Document decisions immediately.
- Treat binary assets as LFS by default.
- Separate research, architecture, and implementation commits.
