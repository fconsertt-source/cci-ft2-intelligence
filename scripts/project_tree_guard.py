#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/project_tree_guard.py
-----------------------------

Generates an immutable Project‑Tree DTO and makes it easy to push that
DTO into the Guard report of any use‑case.

Typical usage inside a use‑case:

    from src.reporting.guard import guard_scope
    from scripts.project_tree_guard import generate_project_tree_dto

    with guard_scope("EvaluateColdChainSafety") as guard:
        tree_dto = generate_project_tree_dto(".", markdown=True, max_depth=10)
        guard.add_dto(tree_dto)

The DTO contains three fields:
* ``root`` – absolute path of the scanned directory.
* ``tree_markdown`` – fenced‑code Markdown (GitHub renders it nicely).
* ``tree_plain``    – plain‑text version (handy for CLI output).

Both representations are stored in the Guard‑report (JSON/CSV/Snapshot)
so they travel with every other DTO produced by the use‑case.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional

# ----------------------------------------------------------------------
#  Configuration – what to ignore while walking the tree
# ----------------------------------------------------------------------
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "env",
    ".venv",
    ".env",
    "node_modules",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".egg-info",
    "reports",
    "logs",
    ".tox",
    "htmlcov",
    "site-packages",
    "pip-wheel-metadata",
}
IGNORE_FILES = {".DS_Store", "Thumbs.db"}


# ----------------------------------------------------------------------
#  DTO – immutable, implements the BaseDTO protocol
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ProjectTreeDTO:
    """
    Immutable DTO that holds two textual representations of the same tree.
    The class implements ``to_dict()`` so it can be consumed by the Guard
    writer exactly like every other DTO in the code‑base.
    """

    root: str  # absolute path that was scanned
    tree_markdown: str  # Markdown fenced‑code block
    tree_plain: str  # plain‑text version

    def to_dict(self) -> Mapping[str, Any]:
        """Return a JSON‑serialisable mapping (required by GuardWriter)."""
        return asdict(self)


# ----------------------------------------------------------------------
#  Low‑level helpers (ignore logic, tree walk)
# ----------------------------------------------------------------------
def _should_ignore(path: Path) -> bool:
    """
    Returns True if *path* or any of its parent directories belong to the
    ignore lists.
    """
    parts = {p.name for p in path.parents} | {path.name}
    return any(ign in parts for ign in IGNORE_DIRS) or path.name in IGNORE_FILES


def _iter_children(root: Path) -> Iterable[Path]:
    """Yield children of *root* in a deterministic (sorted) order."""
    try:
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if _should_ignore(child):
                continue
            yield child
    except PermissionError:
        # Rare in CI, but we silently skip the folder
        return


def _tree_lines(
    root: Path,
    prefix: str = "",
    is_last: bool = True,
    depth: int = 0,
    max_depth: Optional[int] = None,
) -> List[str]:
    """
    Recursively build a list of lines that represent the tree.

    Parameters
    ----------
    root      : Path – directory or file currently processed.
    prefix    : str – visual prefix (branches) built by the recursion.
    is_last   : bool – whether *root* is the last entry of its parent.
    depth     : int – current recursion depth.
    max_depth : int | None – stop recursing when depth >= max_depth.
    """
    connector = "└── " if is_last else "├── "
    lines = [f"{prefix}{connector}{root.name}"]

    if root.is_dir():
        if max_depth is not None and depth >= max_depth:
            # Indicate that the tree is truncated
            lines.append(f"{prefix}{'    ' if is_last else '│   '}…")
            return lines

        child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
        children = list(_iter_children(root))
        for idx, child in enumerate(children):
            child_is_last = idx == len(children) - 1
            lines.extend(
                _tree_lines(
                    child,
                    prefix=child_prefix,
                    is_last=child_is_last,
                    depth=depth + 1,
                    max_depth=max_depth,
                )
            )
    return lines


def _render_tree(lines: List[str], markdown: bool) -> str:
    """Wrap the lines in a fenced block if markdown=True."""
    tree = "\n".join(lines)
    if markdown:
        return f"```tree\n{tree}\n```"
    return tree


# ----------------------------------------------------------------------
#  Public API – generate the DTO
# ----------------------------------------------------------------------
def generate_project_tree_dto(
    start_dir: str | Path = ".",
    *,
    markdown: bool = True,
    max_depth: Optional[int] = None,
) -> ProjectTreeDTO:
    """
    Build the ProjectTreeDTO for *start_dir*.

    Parameters
    ----------
    start_dir : str | Path
        Directory that will be scanned (default = current working dir).
    markdown : bool
        When True the ``tree_markdown`` field contains a fenced‑code block.
    max_depth : int | None
        Stop recursing deeper than *max_depth* levels.

    Returns
    -------
    ProjectTreeDTO
        Immutable DTO ready to be passed to ``guard.add_dto``.
    """
    start_path = Path(start_dir).resolve()
    if not start_path.is_dir():
        raise FileNotFoundError(f"{start_dir} does not exist or is not a directory")

    # Build the line list once – reuse for both representations
    raw_lines = _tree_lines(start_path, is_last=True, depth=0, max_depth=max_depth)

    tree_md = _render_tree(raw_lines, markdown=True) if markdown else ""
    tree_plain = _render_tree(raw_lines, markdown=False)

    return ProjectTreeDTO(
        root=str(start_path),
        tree_markdown=tree_md,
        tree_plain=tree_plain,
    )


# ----------------------------------------------------------------------
#  CLI – for ad‑hoc generation (outside Guard)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate an immutable Project‑Tree DTO (Guard‑compatible)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to scan (default = current working dir).",
    )
    parser.add_argument(
        "--md",
        action="store_true",
        help="Emit Markdown (fenced‑code) instead of plain text.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Maximum depth to display (default = unlimited).",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Print the plain‑text version (ignores --md).",
    )
    args = parser.parse_args()

    dto = generate_project_tree_dto(
        args.path,
        markdown=args.md,
        max_depth=args.depth,
    )
    # CLI is primarily for debugging, so we just print what was asked for
    if args.plain:
        print(dto.tree_plain)
    else:
        # markdown takes precedence if both flags are given
        print(dto.tree_markdown if args.md else dto.tree_plain)
