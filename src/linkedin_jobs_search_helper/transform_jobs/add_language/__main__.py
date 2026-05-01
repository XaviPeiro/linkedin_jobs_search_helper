from __future__ import annotations

import argparse
import logging
from pathlib import Path

from linkedin_jobs_search_helper.logger import configure_logging
from linkedin_jobs_search_helper.transform_jobs.language_detection import LanguageDetector
from .add_description_language import AddDescriptionLanguage

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    default_output_dir = args.input_path.parent if args.input_path.is_file() else args.input_path
    output_path = args.output or default_output_dir / "transformed" / "jobs.json"
    logger.debug(f"Output path: {output_path}")
    logger.debug(f"Input path: {args.input_path}")

    print("hello")
    AddDescriptionLanguage(
        input_path=args.input_path,
        output_path=output_path,
        language_detector=LanguageDetector(),
    )()


if __name__ == "__main__":
    main()
