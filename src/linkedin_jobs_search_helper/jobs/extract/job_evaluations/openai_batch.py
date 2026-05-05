from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from linkedin_jobs_search_helper.common.logger import configure_logging
from linkedin_jobs_search_helper.common.openai_batch_client import OpenAIBatchClient

logger = logging.getLogger(__name__)


def main(
    manifest_path: Path,
    output_path: Path | None = None,
    error_output_path: Path | None = None,
    openai_client: OpenAI | None = None,
) -> dict[str, Any]:
    load_dotenv()
    manifest = OpenAIBatchClient(
        client=openai_client or OpenAI(),
    ).download_batch_results(
        manifest_path=manifest_path,
        output_path=output_path,
        error_output_path=error_output_path,
    )

    logger.info(f"Batch status: {manifest.get('batch', {}).get('status')}")
    if output_path := manifest.get("output_path"):
        logger.info(f"Output file: {output_path}")
    if error_output_path := manifest.get("error_output_path"):
        logger.info(f"Error output file: {error_output_path}")

    return manifest


def entrypoint() -> None:
    configure_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("manifest_path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--error-output", type=Path)
    args = parser.parse_args()

    main(
        manifest_path=args.manifest_path,
        output_path=args.output,
        error_output_path=args.error_output,
    )


if __name__ == "__main__":
    entrypoint()
