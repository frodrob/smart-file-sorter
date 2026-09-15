"""Smart File Sorter: organize messy directories into tidy category folders."""

from .categories import CATEGORIES, category_for
from .sorter import FileEntry, SortPlan, build_plan, apply_plan

__all__ = [
    "CATEGORIES",
    "category_for",
    "FileEntry",
    "SortPlan",
    "build_plan",
    "apply_plan",
]

__version__ = "0.1.0"
