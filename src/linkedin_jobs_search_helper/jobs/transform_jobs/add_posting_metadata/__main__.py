from __future__ import annotations

import argparse
import logging
from pathlib import Path

from linkedin_jobs_search_helper.common.logger import configure_logging
from .add_posting_metadata import AddPostingMetadata

logger = logging.getLogger(__name__)


def main(input_path: Path | None = None, output_path: Path | None = None) -> None:
    configure_logging()

    if input_path is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("input_path", type=Path)
        parser.add_argument("--output", type=Path)
        args = parser.parse_args()

        input_path = args.input_path
        output_path = args.output

    default_output_dir = input_path.parent if input_path.is_file() else input_path
    output_path = output_path or default_output_dir / "2-posting-metadata-added" / "jobs.jsonl"
    logger.debug(f"Output path: {output_path}")
    logger.debug(f"Input path: {input_path}")

    AddPostingMetadata(
        input_path=input_path,
        output_path=output_path,
    )()


if __name__ == "__main__":
    main()
