# src/ingestion/loader.py
from pathlib import Path
from typing import Iterator, Dict
import yaml

from dataclasses import dataclass


@dataclass
class RawDocument:
    """A document read straight off disk – before any splitting."""
    source_path: Path          # e.g. data/sample/aar_001_llab.md
    metadata: Dict             # parsed YAML front‑matter
    body: str                  # plain markdown text after front‑matter
# ----------------------------------------------------------------------


def _parse_frontmatter(text: str) -> tuple[Dict[str, str], str]:
    """
    Split a markdown file that *starts* with a yaml block surrounded by `---`.
    Returns (metadata_dict, body_text).
    If no front‑matter exists the whole file is returned as ``body``.
    """
    if not text.startswith("---"):
        return {}, text

    # split on the first three hyphens
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        metadata = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:               # malformed yaml → ignore
        metadata = {}

    body = parts[2].strip()
    return metadata, body


def load_corpus(root_dir: Path) -> Iterator[RawDocument]:
    """
    Walk ``root_dir`` recursively, yielding a ``RawDocument`` for every ``*.md``.
    """
    for md_file in sorted(root_dir.rglob("*.md")):
        raw_text = md_file.read_text(encoding="utf-8")
        metadata, body = _parse_frontmatter(raw_text)
        yield RawDocument(source_path=md_file, metadata=metadata, body=body)
