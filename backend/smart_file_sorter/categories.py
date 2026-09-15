"""Mapping between file extensions and human-friendly categories.

The mapping is intentionally data-driven so new file types can be supported by
editing a single table rather than touching the sorting logic.
"""

from __future__ import annotations

import os

# Ordered mapping of category name -> set of lowercased extensions (no dot).
CATEGORIES: dict[str, set[str]] = {
    "Images": {"jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "heic", "tiff", "ico"},
    "Documents": {"pdf", "doc", "docx", "txt", "md", "rtf", "odt", "tex", "epub"},
    "Spreadsheets": {"xls", "xlsx", "csv", "ods", "tsv"},
    "Presentations": {"ppt", "pptx", "odp", "key"},
    "Audio": {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma"},
    "Video": {"mp4", "mov", "avi", "mkv", "webm", "flv", "wmv", "m4v"},
    "Archives": {"zip", "tar", "gz", "bz2", "7z", "rar", "xz", "tgz"},
    "Code": {
        "py", "js", "ts", "tsx", "jsx", "java", "c", "cpp", "h", "go", "rs",
        "rb", "php", "sh", "html", "css", "json", "yaml", "yml", "toml", "sql",
    },
    "Data": {"db", "sqlite", "parquet", "log", "xml", "ndjson"},
}

# Files whose type we cannot confidently determine land here.
FALLBACK_CATEGORY = "Other"


def _extension(filename: str) -> str:
    """Return the lowercased extension (without the dot) for a filename."""
    name = os.path.basename(filename)
    # Handle dotfiles like ".gitignore" which have no real extension.
    if name.startswith(".") and name.count(".") == 1:
        return ""
    _, ext = os.path.splitext(name)
    return ext.lstrip(".").lower()


def category_for(filename: str) -> str:
    """Classify a single filename into one of the known categories.

    Unknown or extension-less files are grouped under :data:`FALLBACK_CATEGORY`.
    """
    ext = _extension(filename)
    if not ext:
        return FALLBACK_CATEGORY
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return FALLBACK_CATEGORY
