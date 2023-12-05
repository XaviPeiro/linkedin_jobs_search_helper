import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import ClassVar, Any

from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from domain.criteria.criteria import ICriteria
from domain.notifier import Notifier
from elements_paths import JobsElements
from logger import app_logger, easy_to_apply_logger


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
    def get_job_url(self) -> str:
        ...

    @abstractmethod
    def is_job_discarded(self) -> bool:
        ...

    @abstractmethod
    def is_easy_to_apply(self) -> bool:
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
    # Makes no sense to place here actions related to concrete crawlers, so the receiver is Selenium. However, as long
    # as I do not intend to add any other crawler I will leave it like this for the nonce.
    net_navigator: WebDriver

    def linkedin_discard_job(self):
        try:
            discard_btn = WebDriverWait(self.net_navigator, 5).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, JobsElements.discard_selected_job_css))
            )
        except TimeoutException as te:
            app_logger.error(f"Discard button not found. Selector: {JobsElements.discard_selected_job_css}")
            raise te

        discard_btn.click()

    def get_job_description(self) -> str:
        job_descr_view_class = "jobs-description__container"
        job_descr: str = self.net_navigator.find_element(By.CLASS_NAME, job_descr_view_class).text
        return job_descr

    def get_job_title(self) -> str:
        job_title: str = self.net_navigator.find_element(By.CSS_SELECTOR, JobsElements.selected_job_card_title_css).text
        return job_title

    def get_job_url(self) -> str:
        return self.net_navigator.current_url

    def is_job_discarded(self) -> bool:
        # TODO: I have to wait til the DOM is refreshed due to the discard action is triggered just bf this action.
        #  OBVIOUSLY THIS IS A BOTCH. IMPLICIT DEPENDENCY < EXPLICIT DEPENDENCY
        time.sleep(3)
        classes: str = self.net_navigator.find_element(By.CSS_SELECTOR, JobsElements.selected_job_css).get_attribute("class")
        return JobsElements.discarded_job_card_css[1:] in classes

    def is_easy_to_apply(self) -> bool:
        try:
            btn = self.net_navigator.find_element(By.XPATH, JobsElements.easy_to_apply_job_button)
        except NoSuchElementException as non_easy_to_apply_job:
            return False
        return True




@dataclass
class LinkedinDiscardJobCommand(Command):
    criteria: list[ICriteria]
    net_navigator: CrawlerReceiver
    notifier: Notifier
    _action_name: ClassVar[str] = "DISCARD JOB"  # field(init=False, default="DISCARD JOB")

    def __str__(self):
        return f"Action: {self._action_name}."

    """
        Isn't possible to manually undo the "discard" action, so the btn only appears after clicking discard.
        However, it can be done by requesting to the proper endpoint.
    """
    def __call__(self):
        app_logger.info(f"Executing {str(self)} for {self.net_navigator.get_job_title()}")
        # TODO: Will be nice to have track of processed elements in order to repeat the same analysis
        #  over the already processed element thus reducing the time it takes and reqs to openai.
        #  !!!NOT IN THIS FUNCTION.!!!!

        # TODO: Should I separate actions that requires change state and those that do not? Pass the job descr instead
        #  of depending on the net navigator?
        job_url = self.net_navigator.get_job_url()
        message = "Discarded: {answer}; " + f"Job: {self.net_navigator.get_job_title()}; JobUrl: {job_url}"
        job_descr = self.net_navigator.get_job_description()
        job_title = self.net_navigator.get_job_title()
        # TODO: The term "criteria" is used as JobDescriptionOAICriteria.criteria (class and yaml) as the
        #  different algs to to discard (JobDescriptionOAICriteria is ne of them, JobDescriptionOAICriteria). CONFUSING.
        for criteria in self.criteria:
            answer: [bool, None] = criteria.apply(entities=[job_title + "\n\n" + job_descr])[0]
            if answer is True:
                self.net_navigator.linkedin_discard_job()
                app_logger.info("DISCARDED")
            elif answer is False:
                # TODO: The logging thing should be abstracted and I could/should use the python's logger.
                app_logger.info("NOT DISCARDED")
                self.log_not_discarded_job()
                # if self.is_easy_to_apply() is True:
                #     with open(f"./logs/EASY-jobs-to-apply-{date.today()}.txt", mode="a+") as daily_file:
                #         daily_file.write(f"{self.net_navigator.get_job_url()}\n")
                # else:
                #     with open(f"./logs/NOTEASY-jobs-to-apply-{date.today()}.txt", mode="a+") as daily_file:
                #         daily_file.write(f"{self.net_navigator.get_job_url()}\n")
                # Write data to jobs that has not been discarded
                #     self.net_navigator.linkedin_discard_job()
                #     app_logger.info("DISCARDED BECAUSE IT HAS BEEN PERSISTED TO THE LIST 'TO APPLY'")
            else:

                # The model is returning an unexpected message.
                app_logger.info("NOT DISCARDED - Because unexpected answer from OPENAI.")
            self.notifier.notify(message=message.format(answer=answer))

    def log_not_discarded_job(self):
        # TODO: refactor
        jobs_to_apply_logger = logging.getLogger("jobs-to-apply")
        if self.is_easy_to_apply() is True:
            easy_to_apply_logger.info(f"{self.net_navigator.get_job_url()}\n")
            app_logger.info(f"{self.net_navigator.get_job_url()}\n")
        else:
            jobs_to_apply_logger.info(f"{self.net_navigator.get_job_url()}\n")
            app_logger.info(f"{self.net_navigator.get_job_url()}\n")

        self.net_navigator.linkedin_discard_job()
        app_logger.info("DISCARDED BECAUSE IT HAS BEEN PERSISTED TO THE LIST 'TO APPLY'")

    def is_easy_to_apply(self) -> bool:
        res = self.net_navigator.is_easy_to_apply()
        return res


@dataclass
class NotifyJobsRelevanceCommand(Command):
    criteria: list[ICriteria]
    notifier: Notifier
    _action_name: ClassVar[str] = "NOTIFY JOB RELEVANCE"  # field(init=False, default="DISCARD JOB")
    net_navigator: CrawlerReceiver

    def __call__(self):
        app_logger.info(f"Executing {str(self)} for {self.net_navigator.get_job_title()}")
        job_url = self.net_navigator.get_job_url()
        message = "Score: {score}; " + f"Job: {self.net_navigator.get_job_title()}; JobUrl: {job_url}"
        job_descr = self.net_navigator.get_job_description()

        is_discarded = self.net_navigator.is_job_discarded()
        if is_discarded is False:
            for criteria in self.criteria:
                answer: [bool, None] = criteria.apply(entities=[job_descr])[0]
                self.notifier.notify(message=message.format(score=answer))
