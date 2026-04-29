import os
from pathlib import Path
import pytest

@pytest.fixture(scope="session")
def TESTS_ROOT_DIR() -> Path:
    return Path(os.path.dirname(__file__))


@pytest.fixture(scope="session")
def DATASET_PATH(TESTS_ROOT_DIR) -> Path:
    DATASET_PATH = (
            TESTS_ROOT_DIR
            / "test_datasets"
            / "execution#0.json"
    )
    return DATASET_PATH
