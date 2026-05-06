from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from linkedin_jobs_search_helper.jobs.extract.scanners.commands.command import SeleniumReceiver
from linkedin_jobs_search_helper.jobs.extract.scanners.linkedin.elements_paths import JobsElements


class FakeElement:
    def __init__(self, text: str):
        self._text = text

    @property
    def text(self) -> str:
        return self._text


class StaleElement:
    @property
    def text(self) -> str:
        raise StaleElementReferenceException("stale")


class FakeDriver:
    def __init__(self, *, find_elements_results=None, find_element_results=None):
        self.find_elements_results = list(find_elements_results or [])
        self.find_element_results = list(find_element_results or [])

    def find_elements(self, by: str, value: str):
        assert by == By.CSS_SELECTOR
        assert value == JobsElements.job_workplace_type_css
        return self.find_elements_results.pop(0)

    def find_element(self, by: str, value: str):
        if not self.find_element_results:
            raise NoSuchElementException("not found")

        result = self.find_element_results.pop(0)
        if isinstance(result, Exception):
            raise result

        return result


def test_get_workplace_type_retries_after_stale_element():
    receiver = SeleniumReceiver(
        net_navigator=FakeDriver(
            find_elements_results=[
                [StaleElement()],
                [FakeElement("Remote")],
            ],
        )
    )

    assert receiver.get_workplace_type() == "remote"


def test_get_extra_data_tolerates_stale_optional_metadata():
    receiver = SeleniumReceiver(
        net_navigator=FakeDriver(
            find_element_results=[
                StaleElementReferenceException("stale"),
                FakeElement("Germany · 7 hours ago"),
            ],
            find_elements_results=[
                [],
                [],
                [],
            ],
        )
    )

    assert receiver.get_extra_data() == {
        "top_card_tertiary_description": "Germany · 7 hours ago",
        "workplace_type": None,
    }
