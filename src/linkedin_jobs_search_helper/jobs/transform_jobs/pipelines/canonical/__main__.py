from __future__ import annotations

import argparse
import logging
from pathlib import Path

from linkedin_jobs_search_helper.common.logger import configure_logging
from linkedin_jobs_search_helper.common.openai_batch_client import DEFAULT_JOBS_PER_REQUEST
from linkedin_jobs_search_helper.jobs.transform_jobs.create_batch.__main__ import DEFAULT_MODEL
from .canonical import CanonicalPipeline

logger = logging.getLogger(__name__)


def main(
    input_path: Path | None = None,
    output_dir: Path | None = None,
    instruction_path: Path | None = None,
    model: str | None = None,
    sources_path: Path | None = None,
    jobs_per_request: int | None = None,
) -> None:
    configure_logging()

    if input_path is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("input_path", type=Path)
        parser.add_argument("--output-dir", type=Path)
        parser.add_argument("--instruction-path", type=Path, required=True)
        parser.add_argument("--model", default=DEFAULT_MODEL)
        parser.add_argument("--sources", type=Path, default=Path("user_data"))
        parser.add_argument("--jobs-per-request", type=int)
        args = parser.parse_args()

        input_path = args.input_path
        output_dir = args.output_dir
        instruction_path = args.instruction_path
        model = args.model
        sources_path = args.sources
        jobs_per_request = args.jobs_per_request

    if instruction_path is None:
        raise ValueError("instruction_path is required")

    default_output_dir = input_path.parent if input_path.is_file() else input_path
    output_dir = output_dir or default_output_dir / "canonical"
    model = model or DEFAULT_MODEL
    jobs_per_request = jobs_per_request or DEFAULT_JOBS_PER_REQUEST

    logger.info(f"Input path: {input_path}")
    logger.info(f"Output dir: {output_dir}")
    logger.info(f"Instruction path: {instruction_path}")
    logger.info(f"Sources path: {sources_path}")

    execution_dir = CanonicalPipeline(
        input_path=input_path,
        output_dir=output_dir,
        instruction_path=instruction_path,
        model=model,
        sources_path=sources_path,
        jobs_per_request=jobs_per_request,
    )()

    logger.info(f"Pipeline output: {execution_dir}")


if __name__ == "__main__":
    main()
