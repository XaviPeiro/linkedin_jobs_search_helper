from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from linkedin_jobs_search_helper.common.openai_batch_client import (
    DEFAULT_JOBS_PER_REQUEST,
    OpenAIBatchClient,
    StoredBatchJob,
)


class CreateBatch:
    def __init__(
        self,
        input_path: Path,
        output_dir: Path,
        instruction: str,
        model: str,
        sources_path: Path | None = None,
        jobs_per_request: int = DEFAULT_JOBS_PER_REQUEST,
        openai_client: OpenAI | None = None,
    ):
        self.input_path = input_path
        self.output_dir = output_dir
        self.instruction = instruction
        self.model = model
        self.sources_path = sources_path
        self.jobs_per_request = jobs_per_request
        load_dotenv()
        self.openai_client = openai_client or OpenAI()

    def __call__(self) -> StoredBatchJob:
        return OpenAIBatchClient(client=self.openai_client).create_chat_completion_batch(
            input_jsonl_path=self.input_path,
            instruction=self.instruction,
            model=self.model,
            storage_dir=self.output_dir,
            sources=read_source_documents(self.sources_path),
            jobs_per_request=self.jobs_per_request,
        )


def read_source_documents(sources_path: Path | None) -> list[dict[str, str]]:
    if sources_path is None:
        return []

    if sources_path.is_file():
        paths = [sources_path]
    else:
        paths = sorted(path for path in sources_path.iterdir() if path.is_file())

    return [
        {
            "name": path.name,
            "content": path.read_text(),
        }
        for path in paths
    ]
