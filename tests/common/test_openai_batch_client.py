import json
from dataclasses import dataclass
from pathlib import Path

from linkedin_jobs_search_helper.common.openai_batch_client import (
    CHAT_COMPLETIONS_BATCH_ENDPOINT,
    OpenAIBatchClient,
    write_chat_completion_batch_input,
)


RAW_LINKEDIN_JOBS_FIXTURE = Path("tests/test_datasets/linkedin_raw_extra_data_2026-05-02.jsonl")


def test_write_chat_completion_batch_input_from_real_jobs_jsonl(tmp_path):
    output_file = tmp_path / "openai-batch" / "jobs.batch-input.jsonl"

    write_chat_completion_batch_input(
        input_jsonl_path=RAW_LINKEDIN_JOBS_FIXTURE,
        output_jsonl_path=output_file,
        instruction="Extract structured job data.",
        model="gpt-4o-mini",
        sources=[{"name": "cv.md", "content": "Python developer CV"}],
    )

    batch_requests = [
        json.loads(line)
        for line in output_file.read_text().splitlines()
        if line.strip()
    ]
    first_request = batch_requests[0]
    custom_ids = [request["custom_id"] for request in batch_requests]
    first_user_payload = json.loads(first_request["body"]["messages"][1]["content"])
    first_user_job = first_user_payload["job"]

    assert len(batch_requests) == 25
    assert len(custom_ids) == len(set(custom_ids))
    assert first_request["custom_id"] == "job-1-4409802662"
    assert first_request["method"] == "POST"
    assert first_request["url"] == CHAT_COMPLETIONS_BATCH_ENDPOINT
    assert first_request["body"]["model"] == "gpt-4o-mini"
    assert first_request["body"]["response_format"]["type"] == "json_schema"
    assert first_request["body"]["response_format"]["json_schema"]["name"] == "JobEvaluation"
    assert first_request["body"]["response_format"]["json_schema"]["strict"] is True
    assert first_request["body"]["response_format"]["json_schema"]["schema"]["required"] == [
        "id",
        "reason",
        "decision",
    ]
    assert first_request["body"]["messages"][0] == {
        "role": "system",
        "content": "Extract structured job data.",
    }
    assert first_user_payload["sources"] == [
        {"name": "cv.md", "content": "Python developer CV"}
    ]
    assert first_user_job["id"] == 4409802662
    assert first_user_job["extra_data"]["top_card_tertiary_description"] == (
        "Germany · 4 hours ago · 4 people clicked apply\nResponses managed off LinkedIn"
    )


def test_openai_batch_client_uses_sdk_for_batch_lifecycle(tmp_path):
    input_file = tmp_path / "jobs.jsonl"
    storage_dir = tmp_path / "openai-batch"
    input_file.write_text(
        json.dumps(
            {
                "id": 4409802662,
                "description": "We are looking for a Python engineer.",
                "title": "Python Engineer",
            }
        )
    )
    sdk_client = FakeOpenAIClient()
    client = OpenAIBatchClient(client=sdk_client)

    stored_batch = client.create_chat_completion_batch(
        input_jsonl_path=input_file,
        instruction="Extract structured job data.",
        model="gpt-4o-mini",
        storage_dir=storage_dir,
    )
    manifest = json.loads(stored_batch.manifest_path.read_text())

    assert sdk_client.files.uploaded_path.name == "jobs.batch-input.jsonl"
    assert sdk_client.files.uploaded_purpose == "batch"
    assert sdk_client.batches.created_input_file_id == "file_123"
    assert sdk_client.batches.created_endpoint == CHAT_COMPLETIONS_BATCH_ENDPOINT
    assert sdk_client.batches.created_completion_window == "24h"
    assert stored_batch.batch_id == "batch_123"
    assert manifest["batch_id"] == "batch_123"
    assert manifest["input_file_id"] == "file_123"


def test_openai_batch_client_downloads_results_with_sdk(tmp_path):
    manifest_path = tmp_path / "batch_123.json"
    manifest_path.write_text(
        json.dumps(
            {
                "batch_id": "batch_123",
                "batch": {},
            }
        )
    )
    sdk_client = FakeOpenAIClient()
    client = OpenAIBatchClient(client=sdk_client)

    manifest = client.download_batch_results(manifest_path=manifest_path)

    output_path = manifest_path.with_suffix(".output.jsonl")
    assert sdk_client.batches.retrieved_batch_id == "batch_123"
    assert sdk_client.files.downloaded_file_id == "file_output_123"
    assert output_path.read_text() == '{"custom_id":"job-1"}\n'
    assert manifest["output_path"] == str(output_path)


@dataclass
class FakeOpenAIModel:
    id: str
    output_file_id: str | None = None
    error_file_id: str | None = None

    def model_dump(self, mode: str) -> dict:
        return {
            "id": self.id,
            "output_file_id": self.output_file_id,
            "error_file_id": self.error_file_id,
        }


class FakeFileContent:
    text = '{"custom_id":"job-1"}\n'


class FakeFiles:
    uploaded_path: Path | None = None
    uploaded_purpose: str | None = None
    downloaded_file_id: str | None = None

    def create(self, *, file, purpose: str):
        self.uploaded_path = Path(file.name)
        self.uploaded_purpose = purpose
        return FakeOpenAIModel(id="file_123")

    def content(self, file_id: str):
        self.downloaded_file_id = file_id
        return FakeFileContent()


class FakeBatches:
    created_input_file_id: str | None = None
    created_endpoint: str | None = None
    created_completion_window: str | None = None
    retrieved_batch_id: str | None = None

    def create(
        self,
        *,
        input_file_id: str,
        endpoint: str,
        completion_window: str,
    ):
        self.created_input_file_id = input_file_id
        self.created_endpoint = endpoint
        self.created_completion_window = completion_window
        return FakeOpenAIModel(id="batch_123")

    def retrieve(self, batch_id: str):
        self.retrieved_batch_id = batch_id
        return FakeOpenAIModel(
            id=batch_id,
            output_file_id="file_output_123",
        )


class FakeOpenAIClient:
    def __init__(self):
        self.files = FakeFiles()
        self.batches = FakeBatches()
