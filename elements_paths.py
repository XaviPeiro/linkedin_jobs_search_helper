from abc import ABC


class ElementsPaths(ABC):
    ...


class LoginElements(ElementsPaths):
    submit_btn_xpath: str = '//*[@id="organic-div"]/form/div[3]/button'


class JobsElements(ElementsPaths):
    pages_list_class: str = "artdeco-pagination__pages"
    no_results_class: str = "jobs-search-no-results-banner"
    job_cards_clickable: str = "job-card-container--clickable"
    all_job_cards_xpath: str = "//li[@data-occludable-job-id]"
    discard_job_css: str = "div.job-card-container__action--visible-on-hover > button"
    # job

