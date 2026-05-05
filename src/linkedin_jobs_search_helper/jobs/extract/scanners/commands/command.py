import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from linkedin_jobs_search_helper.jobs.extract.scanners.linkedin.elements_paths import JobsElements

logger = logging.getLogger(__name__)

WORKPLACE_TYPES = {
    "remote": "remote",
    "hybrid": "hybrid",
    "on-site": "in-situ",
}


class CrawlerReceiver(ABC):
    # net_navigator: Any

    @abstractmethod
    def linkedin_discard_job(self):
        ...

    # TODO: Does not make much sense to me to create read attr like this in the receiver.
    #  --> logging: place it in the crawler or command.
    #  --> gather data: something more abstract/generalistic
    @abstractmethod
    def get_job_description(self) -> str:
        ...

    @abstractmethod
    def get_job_title(self) -> str:
        ...

    @abstractmethod
    def get_url(self) -> str:
        ...

    @abstractmethod
    def get_job_id(self) -> str:
        ...

    @abstractmethod
    def get_extra_data(self) -> dict[str, Any]:
        ...


class Command(ABC):
    """
        Not really a Command but the best name found so far.
    """
    net_navigator: CrawlerReceiver

    @abstractmethod
    def __call__(self):
        ...


@dataclass
class SeleniumReceiver(CrawlerReceiver):
    def get_url(self) -> str:
        return self.net_navigator.current_url

    # Makes no sense to place here actions related to concrete crawlers, so the receiver is Selenium. However, as long
    # as I do not intend to add any other crawler I will leave it like this for the nonce.
    net_navigator: WebDriver

    def linkedin_discard_job(self):
        discard_btn = WebDriverWait(self.net_navigator, 5).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, JobsElements.discard_selected_job_css))
        )
        discard_btn.click()

    def get_job_description(self) -> str:
        job_descr_view_class = "jobs-description__container"
        job_descr: str = self.net_navigator.find_element(By.CLASS_NAME, job_descr_view_class).text
        return job_descr

    def get_job_title(self) -> str:
        job_title: str = self.net_navigator.find_element(By.CSS_SELECTOR, JobsElements.selected_job_css).text.split("\n")[0]
        return job_title
        
    def get_job_link(self) -> str:
        job_id = self.get_job_id()
        job_link: str = f"https://www.linkedin.com/jobs/view/{job_id}/"
        return job_link

    def get_job_id(self) -> str:
        return self.net_navigator.find_element(By.CSS_SELECTOR, JobsElements.selected_job_css).get_attribute("data-job-id")

    def get_extra_data(self) -> dict[str, Any]:
        try:
            top_card_tertiary_description = self.net_navigator.find_element(
                By.CSS_SELECTOR,
                JobsElements.job_top_card_tertiary_description_css,
            ).text.strip()
        except NoSuchElementException:
            logger.warning(f"No extra data found for job {self.get_job_id()}")
            top_card_tertiary_description = ""

        return {
            "top_card_tertiary_description": top_card_tertiary_description,
            "workplace_type": self.get_workplace_type(),
        }

    def get_workplace_type(self) -> str | None:
        workplace_elements = self.net_navigator.find_elements(
            By.CSS_SELECTOR,
            JobsElements.job_workplace_type_css,
        )
        for workplace_element in workplace_elements:
            workplace_type = WORKPLACE_TYPES.get(workplace_element.text.strip().lower())
            if workplace_type is not None:
                return workplace_type

        return None
