# Source Import Plan

## Goal

Bring useful existing source material into TitanForge Engine without flooding the repository with temporary files, caches, or unknown binaries.

## First Import Set

Prefer importing:

- README and project notes
- Source code
- Configuration files
- Small sample masks
- Small sample schematics
- Small expected outputs
- Tests or scripts that prove behavior

Avoid importing at first:

- Build caches
- Temporary exports
- Huge renders
- Unlabeled archives
- Dependency folders
- IDE metadata
- Duplicate experiments

## Required From User

The path to the real project/source folder.

Example:

```text
C:\Users\Li2Fox\Documents\Some Project Folder
```

## Import Steps

1. Inventory the folder.
2. Identify file types, sizes, and likely generated folders.
3. Propose what to include, ignore, or place in LFS.
4. Copy or move selected files into the repo.
5. Commit in small groups.
