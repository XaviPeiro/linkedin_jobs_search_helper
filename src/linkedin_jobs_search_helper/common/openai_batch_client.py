import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


CHAT_COMPLETIONS_BATCH_ENDPOINT = "/v1/chat/completions"
DEFAULT_COMPLETION_WINDOW = "24h"


class OpenAIBatchClientError(Exception):
    pass


@dataclass(frozen=True)
class StoredBatchJob:
    manifest_path: Path
    batch_id: str
    input_jsonl_path: Path
    batch_input_jsonl_path: Path


class OpenAIBatchClient:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "OpenAIBatchClient":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise OpenAIBatchClientError("OPENAI_API_KEY is not set")

        return cls(api_key=api_key)

    def create_chat_completion_batch(
        self,
        *,
        input_jsonl_path: Path,
        instruction: str,
        model: str,
        storage_dir: Path,
    ) -> StoredBatchJob:
        storage_dir.mkdir(parents=True, exist_ok=True)
        batch_input_jsonl_path = storage_dir / f"{input_jsonl_path.stem}.batch-input.jsonl"
        write_chat_completion_batch_input(
            input_jsonl_path=input_jsonl_path,
            output_jsonl_path=batch_input_jsonl_path,
            instruction=instruction,
            model=model,
        )

        uploaded_file = self.upload_batch_file(batch_input_jsonl_path)
        batch = self.create_batch(
            input_file_id=uploaded_file["id"],
            endpoint=CHAT_COMPLETIONS_BATCH_ENDPOINT,
        )
        manifest_path = storage_dir / f"{batch['id']}.json"
        _write_json(
            manifest_path,
            {
                "batch_id": batch["id"],
                "input_file_id": uploaded_file["id"],
                "input_jsonl_path": str(input_jsonl_path),
                "batch_input_jsonl_path": str(batch_input_jsonl_path),
                "batch": batch,
            },
        )

        return StoredBatchJob(
            manifest_path=manifest_path,
            batch_id=batch["id"],
            input_jsonl_path=input_jsonl_path,
            batch_input_jsonl_path=batch_input_jsonl_path,
        )

    def upload_batch_file(self, path: Path) -> dict[str, Any]:
        boundary = f"----linkedin-jobs-search-helper-{uuid.uuid4().hex}"
        body = _multipart_form_data(
            boundary=boundary,
            fields={"purpose": "batch"},
            files={"file": path},
        )
        return self._request_json(
            method="POST",
            path="/files",
            body=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    def create_batch(
        self,
        *,
        input_file_id: str,
        endpoint: str = CHAT_COMPLETIONS_BATCH_ENDPOINT,
        completion_window: str = DEFAULT_COMPLETION_WINDOW,
    ) -> dict[str, Any]:
        return self._request_json(
            method="POST",
            path="/batches",
            json_body={
                "input_file_id": input_file_id,
                "endpoint": endpoint,
                "completion_window": completion_window,
            },
        )

    def retrieve_batch(self, batch_id: str) -> dict[str, Any]:
        return self._request_json(method="GET", path=f"/batches/{batch_id}")

    def refresh_manifest(self, manifest_path: Path) -> dict[str, Any]:
        manifest = _read_json(manifest_path)
        batch = self.retrieve_batch(manifest["batch_id"])
        manifest["batch"] = batch
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
        return self._request_bytes(method="GET", path=f"/files/{file_id}/content")

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers = {"Content-Type": "application/json", **(headers or {})}

        response_body = self._request_bytes(
            method=method,
            path=path,
            body=body,
            headers=headers,
        )
        return json.loads(response_body.decode("utf-8"))

    def _request_bytes(
        self,
        *,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        request = Request(
            url=f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                **(headers or {}),
            },
        )

        try:
            with urlopen(request) as response:
                return response.read()
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise OpenAIBatchClientError(f"OpenAI API request failed: {exc.code} {error_body}") from exc


def write_chat_completion_batch_input(
    *,
    input_jsonl_path: Path,
    output_jsonl_path: Path,
    instruction: str,
    model: str,
) -> None:
    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with input_jsonl_path.open() as input_file, output_jsonl_path.open("w") as output_file:
        request_number = 0
        for line in input_file:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            job = json.loads(stripped_line)
            if not isinstance(job, dict):
                raise ValueError("Expected one JSON object per JSONL line")

            request_number += 1
            custom_id = _custom_id_for_job(job=job, request_number=request_number)
            request_body = {
                "custom_id": custom_id,
                "method": "POST",
                "url": CHAT_COMPLETIONS_BATCH_ENDPOINT,
                "body": {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": json.dumps(job, ensure_ascii=False)},
                    ],
                },
            }
            output_file.write(json.dumps(request_body, ensure_ascii=False))
            output_file.write("\n")


def _custom_id_for_job(*, job: dict[str, Any], request_number: int) -> str:
    job_id = job.get("id") or "no-id"
    return f"job-{request_number}-{job_id}"


def _multipart_form_data(*, boundary: str, fields: dict[str, str], files: dict[str, Path]) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for name, path in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{path.name}"\r\n'
                ).encode("utf-8"),
                b"Content-Type: application/octet-stream\r\n\r\n",
                path.read_bytes(),
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
