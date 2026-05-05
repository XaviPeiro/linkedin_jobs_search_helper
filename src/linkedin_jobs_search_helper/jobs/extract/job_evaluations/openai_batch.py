from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from linkedin_jobs_search_helper.common.logger import configure_logging
from linkedin_jobs_search_helper.common.openai_batch_client import OpenAIBatchClient

logger = logging.getLogger(__name__)

DECISIONS = ("MAYBE", "SKIP", "READ")


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
    if output_path_value := manifest.get("output_path"):
        output_path = Path(output_path_value)
        decision_output_paths = split_evaluations_by_decision(output_path)
        manifest["decision_output_paths"] = {
            decision: str(path)
            for decision, path in decision_output_paths.items()
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        logger.info(f"Output file: {output_path}")
        for decision, path in decision_output_paths.items():
            logger.info(f"{decision} file: {path}")
    if error_output_path := manifest.get("error_output_path"):
        logger.info(f"Error output file: {error_output_path}")

    return manifest


def split_evaluations_by_decision(output_path: Path) -> dict[str, Path]:
    decision_output_paths = {
        decision: output_path.with_name(f"{output_path.stem}.{decision}.jsonl")
        for decision in DECISIONS
    }
    evaluations_by_decision = {decision: [] for decision in DECISIONS}

    for evaluation in iter_job_evaluations(output_path):
        decision = str(evaluation.get("decision", "")).upper()
        if decision in evaluations_by_decision:
            evaluations_by_decision[decision].append(evaluation)

    for decision, path in decision_output_paths.items():
        with path.open("w") as output_file:
            for evaluation in evaluations_by_decision[decision]:
                output_file.write(json.dumps(evaluation, ensure_ascii=False))
                output_file.write("\n")

    return decision_output_paths


def iter_job_evaluations(output_path: Path):
    for line in output_path.read_text().splitlines():
        if not line.strip():
            continue

        batch_result = json.loads(line)
        content = _get_message_content(batch_result)
        if content is None:
            continue

        payload = json.loads(content)
        evaluations = payload.get("jobs")
        if isinstance(evaluations, list):
            for evaluation in evaluations:
                if isinstance(evaluation, dict):
                    yield evaluation
        elif isinstance(payload, dict):
            yield payload


def _get_message_content(batch_result: dict[str, Any]) -> str | None:
    choices = (
        batch_result.get("response", {})
        .get("body", {})
        .get("choices", [])
    )
    if not choices:
        return None

    return choices[0].get("message", {}).get("content")


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
