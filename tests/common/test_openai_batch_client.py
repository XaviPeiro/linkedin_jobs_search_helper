import json
from pathlib import Path

from linkedin_jobs_search_helper.common.openai_batch_client import (
    CHAT_COMPLETIONS_BATCH_ENDPOINT,
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
    )

    batch_requests = [
        json.loads(line)
        for line in output_file.read_text().splitlines()
        if line.strip()
    ]
    first_request = batch_requests[0]
    custom_ids = [request["custom_id"] for request in batch_requests]
    first_user_payload = json.loads(first_request["body"]["messages"][1]["content"])

    assert len(batch_requests) == 25
    assert len(custom_ids) == len(set(custom_ids))
    assert first_request["custom_id"] == "job-1-4409802662"
    assert first_request["method"] == "POST"
    assert first_request["url"] == CHAT_COMPLETIONS_BATCH_ENDPOINT
    assert first_request["body"]["model"] == "gpt-4o-mini"
    assert first_request["body"]["messages"][0] == {
        "role": "system",
        "content": "Extract structured job data.",
    }
    assert first_user_payload["id"] == 4409802662
    assert first_user_payload["extra_data"]["top_card_tertiary_description"] == (
        "Germany · 4 hours ago · 4 people clicked apply\nResponses managed off LinkedIn"
    )
