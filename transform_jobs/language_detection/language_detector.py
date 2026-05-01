from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import langid


UNKNOWN_LANGUAGE = "unknown"

DEFAULT_SUPPORTED_LANGUAGES = (
    "de",
    "en",
    "es",
    "fr",
    "it",
    "nl",
    "pl",
)

LINKEDIN_CHROME_LINES = {
    "acerca del empleo",
    "about the job",
}


@dataclass(frozen=True)
class DetectedLanguage:
    language: str
    confidence: float
    scores: dict[str, float]


class LanguageDetector:
    _supported_languages: set[str]
    _top_k: int

    def __init__(
        self,
        supported_languages: Iterable[str] | None = None,
        top_k: int = 5,
    ):
        self._supported_languages = set(
            supported_languages or DEFAULT_SUPPORTED_LANGUAGES
        )
        self._top_k = top_k

    def detect(self, text: str) -> DetectedLanguage:
        normalized_text = _normalize_text(text)

        if not normalized_text:
            return DetectedLanguage(language=UNKNOWN_LANGUAGE, confidence=1.0, scores={})

        ranked_languages = langid.rank(normalized_text)
        scores = {
            language: round(score, 3)
            for language, score in ranked_languages[: self._top_k]
        }

        top_language, _ = ranked_languages[0]
        if top_language not in self._supported_languages:
            return DetectedLanguage(
                language=UNKNOWN_LANGUAGE,
                confidence=1.0,
                scores=scores,
            )

        return DetectedLanguage(
            language=top_language,
            confidence=_confidence_from_ranked_scores(ranked_languages),
            scores=scores,
        )


def _normalize_text(text: str) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and line.strip().casefold() not in LINKEDIN_CHROME_LINES
    ]

    return "\n".join(lines)


def _confidence_from_ranked_scores(
    ranked_languages: list[tuple[str, float]],
) -> float:
    if len(ranked_languages) == 1:
        return 1.0

    top_score = ranked_languages[0][1]
    runner_up_score = ranked_languages[1][1]
    margin = top_score - runner_up_score

    return round(1 / (1 + math.exp(-margin)), 3)
