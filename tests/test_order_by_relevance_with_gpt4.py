import os

from domain.criteria.relevant_job_OAI_criteria import JobDescriptionOAICriteriaRelevance
from tests.fixtures.order_by_relevance.python_backend_location_salary_and_remote.conftest import get_dummy_order_by_relevance_job_descriptions


class FilesReaderIterator:
    def __init__(self, files: list[str]):
        self.files = files

    def __iter__(self):
        return self

    def __next__(self) -> tuple[str, str]:
        next_file: str = self.files.pop(0)
        with open(file=next_file, mode="r") as f:
            return os.path.basename(next_file), f.read()


class TestOrderByRelevanceWithGPT4:
    def test_order_by_relevance_with_dummy_gold_cases(self, get_dummy_order_by_relevance_job_descriptions):
        # TODO: Get CriteriaByRelevance from conftest or testing container
        total_res = []
        order_by_relevance_criteria = JobDescriptionOAICriteriaRelevance()
        for file_name, dummy_descr in get_dummy_order_by_relevance_job_descriptions:
            res = order_by_relevance_criteria.apply(entities=[dummy_descr])

        # assert order


