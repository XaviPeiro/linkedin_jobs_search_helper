from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from domain.criteria import JobNLPCriteria
from domain.notifier import Notifier
from elements_paths import JobsElements
from logger import app_logger
from openai_api import OpenAIClient

"""
    Not really a Command but the best name found so far.
"""


class Command(ABC):

    @abstractmethod
    def __call__(self):
        ...


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


@dataclass
class LinkedinDiscardJobCommand(Command):
    open_ai_client: OpenAIClient
    net_navigator: CrawlerReceiver
    notifier: Notifier
    # ask_openai_service: Callable[[str], dict]
    open_ai_client: OpenAIClient
    criteria: list

    _action_name: ClassVar[str] = "DISCARD JOB"  # field(init=False, default="DISCARD JOB")

    def __str__(self):
        return f"Action: {self._action_name}."

    def __call__(self):
        app_logger.info(f"Executing {str(self)} for {self.net_navigator.get_job_title()}")
        # TODO: Will be nice to have track of processed elements in order to repeat the same analysis
        #  over the already processed element thus reducing the time it takes and reqs to openai.
        #  !!!NOT IN THIS FUNCTION.!!!!

        # Isn't possible to manually undo the "discard" action, so the btn only appears after clicking discard.
        # However, it can be done by requesting to the proper endpoint.
        # Answer the following yes-no questions, I do not want you to respond anything else than yes or no.
        NLP_criteria = JobNLPCriteria(open_ai_client=self.open_ai_client, criteria=self.criteria)
        answer: [bool, None] = NLP_criteria.apply(entities=[self.net_navigator.get_job_description()])[0]
        # To keep it cheap I use 3.5-turbo. Besides that, I want to get only True/False as response, but the only way
        # I've found to do that is specifying "this is a yes-no question" (pregunta directa total); exchanging
        # yes/no byt True/False doesn't work. The "Yes/No" answer comes with a final dot, so it has to be trimmed.

        # TODO: I need a simple response. RN depends on the message set in the app_config.yaml... It is not ideal.
        #  Sometimes it adds kinda explanation, a workaround can be just checking the first word.
        if answer is True:
            self.net_navigator.linkedin_discard_job()
            app_logger.info("DISCARDED")
        elif answer is False:
            app_logger.info("NOT DISCARDED")
        else:
            # The model is returning an unexpected message.
            app_logger.info("NOT DISCARDED - Because unexpected answer from OPENAI.")


"""
You will be provided with IT job descriptions and you will be asked many questions about it in order to know if I should discard this job offer or not. 

For each list of questions you receive from a job offer do the following:
1. - Evaluate every single question independently, ie, check if they would get a positive or negative answer. If you are not sure about how a question should be evaluated, assume it will have a negative answer.
2. - If the answer to one of the previously evaluated questions is positive, respond a single "yes", if any of the previous questions has 
 a negative answer, respond "no".

Remember to answer a single "yes" or "no", according to the rules defined above.
"""

"""
You will be provided with IT job descriptions and you will be asked many questions about it in order to know if I should discard this job offer or not. Do not guess, be strict and stick to the job description.

For each list of questions you receive from a job offer do the following:
1. - Evaluate every single question independently, ie, check if they would get a positive or negative answer. If you are not sure about how a question should be evaluated, assume it will have a negative answer.

2. - Finally, write "yes" if the answer to any of them is yes, otherwise write "no".

Remember to answer a single "yes" or "no", according to the rules defined above.
"""