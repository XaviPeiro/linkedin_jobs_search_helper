from __future__ import annotations

import json
from collections.abc import Iterator
from itertools import chain
from pathlib import Path
from typing import Any


SUPPORTED_COLLECTED_FILE_SUFFIXES = {".jsonl"}


def iter_collected_job_files(collected_jobs_root: Path, supported_files_suffixes: set|None = None) -> Iterator[Path]:

    print("iter_collected_job_files")
    print(collected_jobs_root, collected_jobs_root.suffix)
    supported_files_suffixes = supported_files_suffixes or SUPPORTED_COLLECTED_FILE_SUFFIXES
    if collected_jobs_root.is_file():
        if collected_jobs_root.suffix in supported_files_suffixes:
            yield collected_jobs_root
        return

    print(list(collected_jobs_root.rglob("raw/*")) )
    # Every .jsonl in the dir provided AND every .jsonl under any raw/ dir under the dir provided
    for path in chain(collected_jobs_root.glob("*"), collected_jobs_root.rglob("raw/*")):
        print(path)
        if path.is_file() and path.suffix in supported_files_suffixes:
            yield path


def iter_json_objects(text: str) -> Iterator[dict[str, Any]]:
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        item = json.loads(stripped_line)
        if not isinstance(item, dict):
            raise ValueError(f"Expected a JSON object on line {line_number}")

        yield item
