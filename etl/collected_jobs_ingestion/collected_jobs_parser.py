from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


SUPPORTED_COLLECTED_FILE_SUFFIXES = {".json", ".txt"}


def iter_collected_job_files(collected_jobs_root: Path) -> Iterator[Path]:
    for path in sorted(collected_jobs_root.glob("*/*")):
        if path.is_file() and path.suffix in SUPPORTED_COLLECTED_FILE_SUFFIXES:
            yield path


def iter_json_objects(text: str) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    index = 0

    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1

        if index >= len(text):
            return

        item, end = decoder.raw_decode(text, index)
        if not isinstance(item, dict):
            raise ValueError("Expected a JSON object")

        yield item
        index = end
