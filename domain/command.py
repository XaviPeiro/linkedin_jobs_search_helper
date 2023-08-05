from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, ClassVar

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from domain.notifier import Notifier
from elements_paths import JobsElements
from logger import app_logger


class CrawlerReceiver(ABC):

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


@dataclass
class SeleniumReceiver(CrawlerReceiver):
    net_navigator: WebDriver

    # Makes no sense to place here actions related to concrete crawlers, so the receiver is Selenium. However, as long
    # as I do not intend to add any other crawler I will leave it like this for the nonce.
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
        job_title: str = self.net_navigator.find_element(By.CSS_SELECTOR, JobsElements.selected_job_card_title_css).text
        return job_title


class Command(ABC):

    @abstractmethod
    def __call__(self):
        ...


@dataclass
class LinkedinDiscardJobCommand(Command):
    net_navigator: CrawlerReceiver
    notifier: Notifier
    ask_openai_service: Callable[[str], dict]
    criteria: str

    _action_name: ClassVar[str] = "DISCARD JOB"  # field(init=False, default="DISCARD JOB")

    def __str__(self):
        return f"Action: {self._action_name}."

    def __call__(self):

        try:
            app_logger.info(f"Executing {str(self)} for {self.net_navigator.get_job_title()}")
        except Exception as e:
            # Just for debugging.
            a=1
        # TODO: Will be nice to have track of processed elements in order to repeat the same analysis
        #  over the already processed element thus reducing the time it takes and reqs to openai.
        #  !!!NOT IN THIS FUNCTION.!!!!

        # DOING: store url from this job in order to later check them if required.
        # Isn't possible to undiscard it manually, so the btn only appears after clicking discard.
        # However, it can be done by requesting to the proper endpoint.

        # Let's assume criteria is a text to search in the descr
        job_descr = self.net_navigator.get_job_description()
        res = self.ask_openai_service(question=self.criteria.format(job_descr))

        answer: str = res["choices"][0]["message"]["content"]
        app_logger.info(f"ANSWER: {answer}")

        # To keep it cheap I use 3.5-turbo. Besides that, I want to get only True/False as response, but the only way
        # I've found to do that is specifying "this is a yes-no question" (pregunta directa total); exchanging
        # yes/no byt True/False doesn't work. The "Yes/No" answer comes with a final dot, so it has to be trimmed.

        # TODO: I need a simple response. RN depends on the message set in the app_config.yaml... It is not ideal.
        #  Sometimes it adds kinda explanation, a workaround can be just checking the first word.
        if answer.lower().strip(".") == "yes":
            app_logger.info("DISCARDED")
            self.net_navigator.linkedin_discard_job()
        elif answer.lower().strip(".") == "no":
            app_logger.info("NOT DISCARDED")
        else:
            # The model is returning an unexpected message.
            app_logger.info("NOT DISCARDED - Because unexpected answer from OPENAI.")
        self.notifier.notify(f"{datetime.now()} - {answer}")



