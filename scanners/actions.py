import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from domain.notifier import Notifier
from elements_paths import JobsElements
from logger import app_logger
from openai_api import OpenAIClient, RateLimitException


# TODO P2: change these lil bitches into Commands and inject dependencies.
def print_job_title(element: WebDriver):
    job_title: str = element.find_element(By.CLASS_NAME, "job-card-list__title").text
    app_logger.info(f"Job title = {job_title}")


# TODO: remove, temporal
print_discard_criteria_count = 0


def discard_job(element: WebElement, criteria: str, notifier: Notifier, openai_client: OpenAIClient) -> None:
    # TODO: Will be nice to have track of processed elements in order to repeat the same analysis
    #  over the already processed element thus reducing the time it takes and reqs to openai.
    #  !!!NOT IN THIS FUNCTION.!!!!

    # DOING: store url from this job in order to later check them if required.
    # Isnt possible to undiscard it manually, so the btn only appears after clicking discard.
    # However it can be done by requesting to the proper endpoint.

    global print_discard_criteria_count
    if print_discard_criteria_count == 0:
        print_discard_criteria_count += 1
        app_logger.info(f"Discard if following criteria is True: \n{criteria}")

    # Let's assume criteria is a text to search in the descr
    job_descr_view_class = "jobs-description__container"
    job_descr: str = element.find_element(By.CLASS_NAME, job_descr_view_class).text
    try:

        # TODO:
        #  - I cannot work from my residence country.
        #  - Linkedin’s filter fails and the job found isn’t demanding the language/s I work with.
        #  - I do not do/know a strong requirement.
        #  - Profile requested or tasks do not fit with my requirements/needs.
        #  All those usecases, a priori, could be done at once, thus saving on requests and tokens.

        res = openai_client.request(message=criteria.format(job_descr))
    except RateLimitException as rle:
        # TODO: this is a retry policy. Should no bet here, move it into the client.
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

    # TODO: I need a simple response. RN depends on the message set in the app_config.yaml... It is not ideal.
    if answer.lower().strip(".") == "yes":
        app_logger.info("DISCARDED")
        # discard job
        element.find_element(By.CSS_SELECTOR, JobsElements.discard_job_css).click()
    else:
        if answer.lower().strip(".") != "no":
            # The model is returning an unexpected message (I request a yes-no response, but sometimes...)
            notifier.notify(f"{datetime.now()} - {answer}")

    """
    curl 'https://www.linkedin.com/voyager/api/jobs/jobPostings/3554205489?decorationId=com.linkedin.voyager.deco.jobs.web.shared.WebJobSearchDismissJobPosting-5' \
      -H 'authority: www.linkedin.com' \
      -H 'accept: application/vnd.linkedin.normalized+json+2.1' \
      -H 'accept-language: en-GB,en;q=0.7' \
      -H 'cookie: ***GET_FROM_BROWSER_DRIVER***' \
      -H 'csrf-token: ajax:7254049410398430053' \
      -H 'referer: https://www.linkedin.com/jobs/search/?currentJobId=3554205489&distance=25&f_SB2=3&f_WT=2&geoId=103644278&keywords=Python%20Software%20Engineer&start=150' \
      -H 'sec-ch-ua: "Not.A/Brand";v="8", "Chromium";v="114", "Brave";v="114"' \
      -H 'sec-ch-ua-mobile: ?0' \
      -H 'sec-ch-ua-platform: "Linux"' \
      -H 'sec-fetch-dest: empty' \
      -H 'sec-fetch-mode: cors' \
      -H 'sec-fetch-site: same-origin' \
      -H 'sec-gpc: 1' \
      -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36' \
      -H 'x-li-deco-include-micro-schema: true' \
      -H 'x-li-lang: es_ES' \
      -H 'x-li-page-instance: urn:li:page:d_flagship3_search_srp_jobs;UiCXSS7hQGOB8Nbbn5Rv+Q==' \
      -H 'x-li-track: {"clientVersion":"1.12.9422","mpVersion":"1.12.9422","osName":"web","timezoneOffset":2,"timezone":"Europe/Madrid","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":1,"displayWidth":1923,"displayHeight":986}' \
      -H 'x-restli-protocol-version: 2.0.0' \
      --compressed
      """


def notify_if_exceptional_fit(element: WebElement, criteria: str, notifier: Notifier, openai_client: OpenAIClient) -> None:
    # Consult to openai is the same as in discard. The only diff is the message (a param) and the following
    # action according to the response.
    # Create a service that encapsulate this. I can create a composition of actions/commands
    # in order to improve the openai requests.
    ...


# TODO: Create an action for "easy-apply" jobs
# TODO: Gather especially interesting jobs
