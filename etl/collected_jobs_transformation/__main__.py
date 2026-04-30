from __future__ import annotations

import argparse
from pathlib import Path

from .add_description_language import AddDescriptionLanguage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    default_output_dir = args.input_path.parent if args.input_path.is_file() else args.input_path
    output_path = args.output or default_output_dir / "transformed" / "jobs.json"
    AddDescriptionLanguage(
        input_path=args.input_path,
        output_path=output_path,
    )()


if __name__ == "__main__":
    main()
