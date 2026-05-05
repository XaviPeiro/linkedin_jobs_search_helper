from __future__ import annotations

import argparse
import logging
from pathlib import Path

from linkedin_jobs_search_helper.common.logger import configure_logging
from .create_batch import CreateBatch

logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gpt-5.4-mini'
def main(
    input_path: Path | None = None,
    output_dir: Path | None = None,
    instruction_path: Path | None = None,
    model: str | None = None,
    sources_path: Path | None = None,
) -> None:
    configure_logging()

    if input_path is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("input_path", type=Path)
        parser.add_argument("--output-dir", type=Path)
        parser.add_argument("--instruction-path", type=Path, required=True)
        parser.add_argument("--model", default=DEFAULT_MODEL)
        parser.add_argument("--sources", type=Path, default=Path("user_data"))
        args = parser.parse_args()

        input_path: Path = args.input_path
        output_dir = args.output_dir
        instruction_path = args.instruction_path
        model = args.model
        sources_path = args.sources

    default_output_dir = input_path.parent if input_path.is_file() else input_path
    output_dir = output_dir or default_output_dir / "openai-batch"
    if instruction_path is None:
        raise ValueError("instruction_path is required")
    instruction = instruction_path.read_text()

    logger.info(f"Input path: {input_path}")
    logger.info(f"Output dir: {output_dir}")
    logger.info(f"Instruction path: {instruction_path}")
    logger.info(f"Sources path: {sources_path}")

    stored_batch = CreateBatch(
        input_path=input_path,
        output_dir=output_dir,
        instruction=instruction,
        model=model,
        sources_path=sources_path,
    )()
    logger.info(f"Batch created: {stored_batch.batch_id}")
    logger.info(f"Manifest: {stored_batch.manifest_path}")


if __name__ == "__main__":
    main()
