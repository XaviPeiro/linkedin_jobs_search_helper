import json
from dataclasses import dataclass
from pathlib import Path

from linkedin_jobs_search_helper.common.openai_batch_client import CHAT_COMPLETIONS_BATCH_ENDPOINT
from linkedin_jobs_search_helper.jobs.transform_jobs.create_batch import __main__ as create_batch_main
from linkedin_jobs_search_helper.jobs.transform_jobs.create_batch.create_batch import CreateBatch


def test_create_batch_creates_openai_batch_manifest(tmp_path):
    input_path = tmp_path / "jobs.jsonl"
    output_dir = tmp_path / "openai-batch"
    sources_path = tmp_path / "user_data"
    sources_path.mkdir()
    (sources_path / "cv.md").write_text("Python developer CV")
    (sources_path / "user_preferences.md").write_text("Remote Python jobs")
    input_path.write_text(
        json.dumps(
            {
                "id": 4409802662,
                "description": "We are looking for a Python engineer.",
                "title": "Python Engineer",
            }
        )
    )
    openai_client = FakeOpenAIClient()

    stored_batch = CreateBatch(
        input_path=input_path,
        output_dir=output_dir,
        instruction="Extract structured job data.",
        model="gpt-4o-mini",
        sources_path=sources_path,
        openai_client=openai_client,
    )()

    manifest = json.loads(stored_batch.manifest_path.read_text())
    batch_input_lines = stored_batch.batch_input_jsonl_path.read_text().splitlines()
    batch_request = json.loads(batch_input_lines[0])

    assert openai_client.files.uploaded_path == stored_batch.batch_input_jsonl_path
    assert openai_client.files.uploaded_purpose == "batch"
    assert openai_client.batches.created_input_file_id == "file_123"
    assert openai_client.batches.created_endpoint == CHAT_COMPLETIONS_BATCH_ENDPOINT
    assert openai_client.batches.created_completion_window == "24h"
    assert stored_batch.batch_id == "batch_123"
    assert manifest["batch_id"] == "batch_123"
    assert batch_request["body"]["model"] == "gpt-4o-mini"
    assert batch_request["body"]["response_format"]["json_schema"]["name"] == "JobEvaluation"
    user_payload = json.loads(batch_request["body"]["messages"][1]["content"])

    assert batch_request["body"]["messages"][0]["content"] == "Extract structured job data."
    assert user_payload["job"]["id"] == 4409802662
    assert user_payload["sources"] == [
        {"name": "cv.md", "content": "Python developer CV"},
        {"name": "user_preferences.md", "content": "Remote Python jobs"},
    ]


def test_create_batch_main_reads_instruction_from_file(tmp_path, monkeypatch):
    input_path = tmp_path / "jobs.jsonl"
    output_dir = tmp_path / "openai-batch"
    instruction_path = tmp_path / "instruction.md"
    input_path.write_text('{"id": 1, "description": "desc", "title": "title"}\n')
    instruction_path.write_text("Extract structured job data from this posting.")
    calls = []

    class FakeCreateBatch:
        def __init__(self, *, input_path, output_dir, instruction, model, sources_path):
            calls.append(
                {
                    "input_path": input_path,
                    "output_dir": output_dir,
                    "instruction": instruction,
                    "model": model,
                    "sources_path": sources_path,
                }
            )

        def __call__(self):
            return FakeStoredBatch()

    class FakeStoredBatch:
        batch_id = "batch_123"
        manifest_path = output_dir / "batch_123.json"

    monkeypatch.setattr(create_batch_main, "configure_logging", lambda: None)
    monkeypatch.setattr(create_batch_main, "CreateBatch", FakeCreateBatch)

    create_batch_main.main(
        input_path=input_path,
        output_dir=output_dir,
        instruction_path=instruction_path,
        model="gpt-4o-mini",
        sources_path=tmp_path / "user_data",
    )

    assert calls == [
        {
            "input_path": input_path,
            "output_dir": output_dir,
            "instruction": "Extract structured job data from this posting.",
            "model": "gpt-4o-mini",
            "sources_path": tmp_path / "user_data",
        }
    ]


@dataclass
class FakeOpenAIModel:
    id: str

    def model_dump(self, mode: str) -> dict:
        return {"id": self.id}


class FakeFiles:
    uploaded_path = None
    uploaded_purpose = None

    def create(self, *, file, purpose: str):
        self.uploaded_path = Path(file.name)
        self.uploaded_purpose = purpose
        return FakeOpenAIModel(id="file_123")


class FakeBatches:
    created_input_file_id = None
    created_endpoint = None
    created_completion_window = None

    def create(self, *, input_file_id: str, endpoint: str, completion_window: str):
        self.created_input_file_id = input_file_id
        self.created_endpoint = endpoint
        self.created_completion_window = completion_window
        return FakeOpenAIModel(id="batch_123")


class FakeOpenAIClient:
    def __init__(self):
        self.files = FakeFiles()
        self.batches = FakeBatches()
