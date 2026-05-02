from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from linkedin_jobs_search_helper.jobs.transform_jobs.add_language.conf import ACCEPTED_INPUT_SUFFIX
from linkedin_jobs_search_helper.jobs.transform_jobs.helpers.collected_jobs_parser import (
    iter_collected_job_files,
    iter_json_objects,
)

logger = logging.getLogger(__name__)

TOP_CARD_TERTIARY_DESCRIPTION_KEY = "top_card_tertiary_description"


class PostingMetadata(BaseModel):
    location: str | None = None
    date_posted: date | None = None
    applicants: int | None = None


class AddPostingMetadata:
    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        reference_date: date | None = None,
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.reference_date = reference_date or date.today() # TODO: nope, from parent dir or, better, add metadata in the raw data collected

    def __call__(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        jobs_counter: int = 0
        with self.output_path.open("w") as output_file:
            for input_file in iter_collected_job_files(self.input_path, ACCEPTED_INPUT_SUFFIX):
                for job in iter_json_objects(input_file.read_text()):
                    jobs_counter += 1
                    enriched_job = self._add_posting_metadata(job)
                    output_file.write(json.dumps(enriched_job, ensure_ascii=False))
                    output_file.write("\n")

        logger.info("Successfully added posting metadata")
        logger.info(f"Jobs processed: {jobs_counter}")
        logger.info(f"Find results in: {self.output_path}")

    def _add_posting_metadata(self, job: dict[str, Any]) -> dict[str, Any]:
        metadata = parse_posting_metadata(
            _get_top_card_tertiary_description(job),
            reference_date=self.reference_date,
        )

        return job | {
            "location": metadata.location,
            "date_posted": metadata.date_posted.isoformat() if metadata.date_posted else None,
            "applicants": metadata.applicants,
        }


def parse_posting_metadata(text: str | None, reference_date: date) -> PostingMetadata:
    segments = _split_segments(text)
    location = _extract_location(segments)
    date_posted = _extract_date_posted(segments, reference_date)
    applicants = _extract_applicants(segments)

    return PostingMetadata(
        location=location,
        date_posted=date_posted,
        applicants=applicants,
    )


def _get_top_card_tertiary_description(job: dict[str, Any]) -> str | None:
    extra_data = job.get("extra_data")
    if not isinstance(extra_data, dict):
        return None

    value = extra_data.get(TOP_CARD_TERTIARY_DESCRIPTION_KEY)
    if value is None:
        return None

    return str(value)


def _split_segments(text: str | None) -> list[str]:
    if not text:
        return []

    normalized_text = text.replace("\n", " · ")
    return [
        segment.strip()
        for segment in normalized_text.split("·")
        if segment.strip()
    ]


def _extract_location(segments: list[str]) -> str | None:
    if not segments:
        return None

    first_segment = segments[0]
    if _looks_like_date_posted(first_segment) or _looks_like_applicants(first_segment) or _looks_like_more_metadata(first_segment):
        return None

    return first_segment


def _extract_date_posted(segments: list[str], reference_date: date) -> date | None:
    for segment in segments:
        if not _looks_like_date_posted(segment):
            continue

        parsed_date = _relative_date_to_date(segment, reference_date)
        if parsed_date is not None:
            return parsed_date

    return None


def _extract_applicants(segments: list[str]) -> int | None:
    for segment in segments:
        if not _looks_like_applicants(segment):
            continue

        applicants_match = re.search(r"\d[\d.,]*", segment)
        if applicants_match is None:
            continue

        return int(re.sub(r"\D", "", applicants_match.group()))

    return None


def _relative_date_to_date(text: str, reference_date: date) -> date | None:
    normalized_text = text.lower()
    if any(token in normalized_text for token in ("just now", "today", "ahora", "hoy")):
        return reference_date

    match = re.search(
        r"(\d+)\s+(minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years"
        r"|minuto|minutos|hora|horas|día|días|dia|dias|semana|semanas|mes|meses|año|años)",
        normalized_text,
    )
    if match is None:
        return None

    amount = int(match.group(1))
    unit = match.group(2)
    days = _unit_to_days(unit, amount)

    if days is None:
        return None

    return reference_date - timedelta(days=days)


def _unit_to_days(unit: str, amount: int) -> int|None:
    if unit in {"minute", "minutes", "hour", "hours", "minuto", "minutos", "hora", "horas"}:
        return 0
    if unit in {"day", "days", "día", "días", "dia", "dias"}:
        return amount
    if unit in {"week", "weeks", "semana", "semanas"}:
        return amount * 7
    if unit in {"month", "months", "mes", "meses"}:
        return amount * 30
    if unit in {"year", "years", "año", "años"}:
        return amount * 365

    logger.warning(f"{unit} is not a valid unit in the job")
    return None



def _looks_like_date_posted(segment: str) -> bool:
    normalized_segment = segment.lower()
    return any(
        token in normalized_segment
        for token in (
            "ago",
            "posted",
            "reposted",
            "hace",
            "publicado",
            "publicada",
        )
    )


def _looks_like_applicants(segment: str) -> bool:
    normalized_segment = segment.lower()
    return any(
        token in normalized_segment
        for token in (
            "applicant",
            "applicants",
            "application",
            "applications",
            "clicked apply",
            "people clicked apply",
            "solicitud",
            "solicitudes",
        )
    )


def _looks_like_more_metadata(segment: str) -> bool:
    normalized_segment = segment.lower()
    return any(
        token in normalized_segment
        for token in (
            "promoted",
            "hirer",
            "actively reviewing",
            "promocionado",
            "técnico de selección",
            "tecnico de seleccion",
            "evaluando solicitudes",
        )
    )
