import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from openai import OpenAI
from openai.lib._parsing import type_to_response_format_param

from linkedin_jobs_search_helper.jobs.evaluate.job_evaluation import JobEvaluations

CHAT_COMPLETIONS_BATCH_ENDPOINT: Literal["/v1/chat/completions"] = "/v1/chat/completions"
DEFAULT_COMPLETION_WINDOW: Literal["24h"] = "24h"
DEFAULT_JOBS_PER_REQUEST = 10


class OpenAIBatchClientError(Exception):
    pass


@dataclass(frozen=True)
class StoredBatchJob:
    manifest_path: Path
    batch_id: str
    input_jsonl_path: Path
    batch_input_jsonl_path: Path


class OpenAIBatchClient:
    client: OpenAI

    def __init__(self, client: OpenAI):
        self.client = client

    def create_chat_completion_batch(
        self,
        *,
        input_jsonl_path: Path,
        instruction: str,
        model: str,
        storage_dir: Path,
        sources: list[dict[str, str]] | None = None,
        jobs_per_request: int = DEFAULT_JOBS_PER_REQUEST,
    ) -> StoredBatchJob:
        storage_dir.mkdir(parents=True, exist_ok=True)
        batch_input_jsonl_path = storage_dir / f"{input_jsonl_path.stem}.batch-input.jsonl"
        write_chat_completion_batch_input(
            input_jsonl_path=input_jsonl_path,
            output_jsonl_path=batch_input_jsonl_path,
            instruction=instruction,
            model=model,
            sources=sources or [],
            jobs_per_request=jobs_per_request,
        )

        batch_input_file = self.upload_batch_file(batch_input_jsonl_path)
        batch =  self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint=CHAT_COMPLETIONS_BATCH_ENDPOINT,
            completion_window=DEFAULT_COMPLETION_WINDOW,
        )
        manifest_path = storage_dir / f"{batch.id}.json"
        _write_json(
            manifest_path,
            {
                "batch_id": batch.id,
                "input_file_id": batch_input_file.id,
                "input_jsonl_path": str(input_jsonl_path),
                "batch_input_jsonl_path": str(batch_input_jsonl_path),
                "batch": _model_to_dict(batch),
            },
        )

        return StoredBatchJob(
            manifest_path=manifest_path,
            batch_id=batch.id,
            input_jsonl_path=input_jsonl_path,
            batch_input_jsonl_path=batch_input_jsonl_path,
        )

    def upload_batch_file(self, path: Path) -> Any:
        with path.open("rb") as batch_input_file:
            return self.client.files.create(
                file=batch_input_file,
                purpose="batch",
            )

    def retrieve_batch(self, batch_id: str) -> Any:
        return self.client.batches.retrieve(batch_id)

    def refresh_manifest(self, manifest_path: Path) -> dict[str, Any]:
        manifest = _read_json(manifest_path)
        batch = self.retrieve_batch(manifest["batch_id"])
        manifest["batch"] = _model_to_dict(batch)
        _write_json(manifest_path, manifest)
        return manifest

    def download_batch_results(
        self,
        *,
        manifest_path: Path,
        output_path: Path | None = None,
        error_output_path: Path | None = None,
    ) -> dict[str, Any]:
        manifest = self.refresh_manifest(manifest_path)
        batch = manifest["batch"]

        output_file_id = batch.get("output_file_id")
        if output_file_id:
            output_path = output_path or manifest_path.with_suffix(".output.jsonl")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(self.download_file_content(output_file_id))
            manifest["output_path"] = str(output_path)

        error_file_id = batch.get("error_file_id")
        if error_file_id:
            error_output_path = error_output_path or manifest_path.with_suffix(".errors.jsonl")
            error_output_path.parent.mkdir(parents=True, exist_ok=True)
            error_output_path.write_bytes(self.download_file_content(error_file_id))
            manifest["error_output_path"] = str(error_output_path)

        _write_json(manifest_path, manifest)
        return manifest

    def download_file_content(self, file_id: str) -> bytes:
        return self.client.files.content(file_id).text.encode("utf-8")


def write_chat_completion_batch_input(
    *,
    input_jsonl_path: Path,
    output_jsonl_path: Path,
    instruction: str,
    model: str,
    sources: list[dict[str, str]] | None = None,
    jobs_per_request: int = DEFAULT_JOBS_PER_REQUEST,
) -> None:
    if jobs_per_request < 1:
        raise ValueError("jobs_per_request must be greater than 0")

    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    sources = sources or []
    jobs = list(_iter_jobs(input_jsonl_path))

    with output_jsonl_path.open("w") as output_file:
        for request_number, jobs_chunk in enumerate(_chunks(jobs, jobs_per_request), start=1):
            request_body = {
                "custom_id": f"jobs-{request_number}",
                "method": "POST",
                "url": CHAT_COMPLETIONS_BATCH_ENDPOINT,
                "body": {
                    "model": model,
                    "response_format": type_to_response_format_param(JobEvaluations),
                    "messages": [
                        {"role": "system", "content": instruction},
                        {
                            "role": "user",
                            "content": json.dumps(
                                {"sources": sources, "jobs": jobs_chunk},
                                ensure_ascii=False,
                            ),
                        },
                    ],
                },
            }
            output_file.write(json.dumps(request_body, ensure_ascii=False))
            output_file.write("\n")


def _iter_jobs(input_jsonl_path: Path) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    with input_jsonl_path.open() as input_file:
        for line in input_file:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            job = json.loads(stripped_line)
            if not isinstance(job, dict):
                raise ValueError("Expected one JSON object per JSONL line")

            jobs.append(job)

    return jobs


def _chunks(jobs: list[dict[str, Any]], chunk_size: int) -> list[list[dict[str, Any]]]:
    return [jobs[index:index + chunk_size] for index in range(0, len(jobs), chunk_size)]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")

    if isinstance(model, dict):
        return model

    return dict(model)
