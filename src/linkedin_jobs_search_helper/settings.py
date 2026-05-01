from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    logs_dir: Path
    openai_unexpected_responses_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(getenv("LJSH_PROJECT_ROOT", _default_project_root())).resolve()
    logs_dir = Path(getenv("LJSH_LOGS_DIR", project_root / "logs")).resolve()

    return Settings(
        project_root=project_root,
        logs_dir=logs_dir,
        openai_unexpected_responses_path=Path(
            getenv("LJSH_OPENAI_UNEXPECTED_RESPONSES_PATH", logs_dir / "openai_unexpected_responses.txt")
        ).resolve(),
    )
