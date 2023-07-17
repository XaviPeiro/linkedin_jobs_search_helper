import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from domain.notificator import Notificator
from elements_paths import JobsElements
from logger import app_logger
from openai_api import OpenAIClient, RateLimitException


# TODO P2: change these lil bitches into Commands and inject dependencies.
def print_job_title(element: WebDriver):
    job_title: str = element.find_element(By.CLASS_NAME, "job-card-list__title").text
    app_logger.info(f"Job title = {job_title}")


# TODO: remove, temporal
print_discard_criteria_count = 0


# TODO: criteria and client to Command init
def discard_job(element: WebDriver, criteria: str, notificator: Notificator, openai_client: OpenAIClient) -> None:
    # TODO: Could be nice to have track of processed elements in order to repeat the same analysis
    #  over the already processed element thus reducing the time it takes and reqs to openai.
    #  !!!NOT IN THIS FUNCTION.!!!!
    global print_discard_criteria_count
    if print_discard_criteria_count == 0:
        print_discard_criteria_count += 1
        app_logger.info(f"Discard if following criteria is True: \n{criteria}")

    # Let's assume criteria is a text to search in the descr
    job_descr_view_class = "jobs-description__container"
    job_descr: str = element.find_element(By.CLASS_NAME, job_descr_view_class).text
    try:
        res = openai_client.request(message=criteria.format(job_descr))
    except RateLimitException as rle:
        app_logger.warn("Openai API Rate limit reached 🤷.")
        remaining_time = 61
        while remaining_time > 0:
            app_logger.warn(f"Let's wait {remaining_time}")
            time.sleep(min(remaining_time, 5))
            remaining_time -= 5

        res = openai_client.request(message=criteria.format(job_descr))

    answer: str = res["choices"][0]["message"]["content"]

    # To keep it cheap I use 3.5-turbo. Besides that, I want to get only True/False as response, but the only way
    # I've found to do that is specifying "this is a yes-no question" (pregunta directa total); exchanging
    # yes/no byt True/False doesn't work. The "Yes/No" answer comes with a final dot, so it has to be trimmed.

    # TODO: I FUCKING NEED YES/NO or TURE/FALSE. Nothing else!!!!
    if answer.lower().strip(".") == "yes":
        app_logger.info("DISCARDED")
        # discard job
        element.find_element(By.CSS_SELECTOR, JobsElements.discard_job_css).click()
    else:
        if answer.lower().strip(".") != "no":
            # TODO: notify. The model is returning an unexpected message (I request a yes-no response, but sometimes...)
            notificator.notify(f"{datetime.now()} - {answer}")


# TODO: Easy to apply job
# TODO: Gather interesting jobs
