from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from etl.language_detection import LanguageDetector

from .models import CollectedJobRow, ExternalJobDocument, NormalizedJob


_LANGUAGE_DETECTOR = LanguageDetector()


def normalize_external_job(
    source_path: Path,
    raw_job: dict,
) -> ExternalJobDocument:
    source = CollectedJobRow.model_validate(raw_job)
    url = str(source.url)
    parsed_url = urlparse(url)
    now = datetime.now(timezone.utc)

    return ExternalJobDocument(
        platform=_platform_from_host(parsed_url.netloc),
        ejib=str(source.id),
        raw_payload=source.model_dump(mode="json"),
        normalized=NormalizedJob(
            title=source.title,
            descr=source.description,
            url=url,
            description_language=_LANGUAGE_DETECTOR.detect(source.description).language,
            location=_extract_best_effort_location(source.description),
            salary=None,
            search_term_used=_first_query_value(parsed_url.query, "keywords"),
            date_collected=_date_collected_from_path(source_path),
        ),
        created_at=now,
        updated_at=now,
    )


def _date_collected_from_path(path: Path) -> date:
    return date.fromisoformat(path.parent.name)


def _first_query_value(query: str, key: str) -> str | None:
    values = parse_qs(query).get(key)
    if not values:
        return None

    return values[0]


def _platform_from_host(host: str) -> str:
    normalized_host = host.casefold()
    if "linkedin." in normalized_host:
        return "linkedin"

    return normalized_host.removeprefix("www.")


def _extract_best_effort_location(description: str) -> str | None:
    for line in description.splitlines():
        stripped_line = line.strip()
        lowered_line = stripped_line.casefold()

        for prefix in ("location:", "based in "):
            if lowered_line.startswith(prefix):
                location = stripped_line[len(prefix):].strip()
                return location or None

    return None
