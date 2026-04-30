from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class CollectedJobRow(BaseModel):
    id: int | str
    url: AnyHttpUrl
    description: str
    title: str

    @field_validator("description", "title")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")

        return value


class NormalizedJob(BaseModel):
    title: str
    descr: str
    url: str
    description_language: str
    location: str | None = None
    salary: str | None = None
    search_term_used: str | None = None
    date_collected: date


class ExternalJobDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    platform: str
    ejib: str
    raw_payload: dict[str, Any]
    normalized: NormalizedJob
    created_at: datetime = Field(alias="created_at")
    updated_at: datetime = Field(alias="updated_at")


class IngestionSummary(BaseModel):
    files_seen: int = 0
    rows_seen: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    rejected_rows: int = 0
    errors: list[str] = Field(default_factory=list)
