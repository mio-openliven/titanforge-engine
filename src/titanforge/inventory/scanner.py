from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path


LFS_EXTENSIONS = {
    ".7z",
    ".blend",
    ".fbx",
    ".jpeg",
    ".jpg",
    ".mca",
    ".mov",
    ".mp4",
    ".nbt",
    ".obj",
    ".ogg",
    ".png",
    ".psd",
    ".rar",
    ".schem",
    ".schematic",
    ".tga",
    ".wav",
    ".zip",
}

IGNORED_DIR_NAMES = {
    ".git",
    ".gradle",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
}


@dataclass(frozen=True)
class FileRecord:
    path: Path
    size: int
    extension: str
    lfs_candidate: bool


@dataclass(frozen=True)
class InventoryReport:
    root: Path
    files: tuple[FileRecord, ...]
    skipped_dirs: tuple[Path, ...]

    @property
    def total_size(self) -> int:
        return sum(file.size for file in self.files)

    @property
    def lfs_files(self) -> tuple[FileRecord, ...]:
        return tuple(file for file in self.files if file.lfs_candidate)

    @property
    def extensions(self) -> Counter[str]:
        return Counter(file.extension or "<none>" for file in self.files)

    @property
    def largest_files(self) -> tuple[FileRecord, ...]:
        return tuple(sorted(self.files, key=lambda file: file.size, reverse=True)[:10])


def scan_inventory(root: Path) -> InventoryReport:
    resolved_root = root.resolve()

    if not resolved_root.exists():
        raise FileNotFoundError(f"Inventory path does not exist: {root}")

    if not resolved_root.is_dir():
        raise NotADirectoryError(f"Inventory path is not a directory: {root}")

    files: list[FileRecord] = []
    skipped_dirs: list[Path] = []

    for path in resolved_root.rglob("*"):
        if should_skip(path, resolved_root):
            if path.is_dir():
                skipped_dirs.append(path.relative_to(resolved_root))
            continue

        if not path.is_file():
            continue

        relative = path.relative_to(resolved_root)
        extension = path.suffix.lower()
        files.append(
            FileRecord(
                path=relative,
                size=path.stat().st_size,
                extension=extension,
                lfs_candidate=extension in LFS_EXTENSIONS,
            )
        )

    return InventoryReport(
        root=resolved_root,
        files=tuple(files),
        skipped_dirs=tuple(skipped_dirs),
    )


def should_skip(path: Path, root: Path) -> bool:
    if path == root:
        return False

    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True

    return any(part in IGNORED_DIR_NAMES for part in relative_parts)


def format_size(size: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{size} B"


def format_inventory_report(report: InventoryReport) -> str:
    lines = [
        f"Inventory: {report.root}",
        f"Files: {len(report.files)}",
        f"Total size: {format_size(report.total_size)}",
        f"LFS candidates: {len(report.lfs_files)}",
        "",
        "Top extensions:",
    ]

    for extension, count in report.extensions.most_common(10):
        lines.append(f"- {extension}: {count}")

    lines.append("")
    lines.append("Largest files:")
    for file in report.largest_files:
        lfs_marker = " [LFS]" if file.lfs_candidate else ""
        lines.append(f"- {file.path} ({format_size(file.size)}){lfs_marker}")

    if report.skipped_dirs:
        lines.append("")
        lines.append("Skipped directories:")
        for directory in report.skipped_dirs[:10]:
            lines.append(f"- {directory}")

    return "\n".join(lines)
