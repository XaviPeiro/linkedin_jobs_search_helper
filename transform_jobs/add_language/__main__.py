from __future__ import annotations
from logger import app_logger
import logging
import argparse
from pathlib import Path

from transform_jobs.language_detection import LanguageDetector
from .add_description_language import AddDescriptionLanguage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    default_output_dir = args.input_path.parent if args.input_path.is_file() else args.input_path
    output_path = args.output or default_output_dir / "transformed" / "jobs.json"
    app_logger.debug(f"Output path: {output_path}")
    app_logger.debug(f"Input path: {args.input_path}")

    print("hello")
    AddDescriptionLanguage(
        input_path=args.input_path,
        output_path=output_path,
        language_detector=LanguageDetector(),
    )()


if __name__ == "__main__":
    main()
