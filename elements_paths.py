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
    all_not_dismissed_job_cards_xpath: str = "//li[@data-occludable-job-id and not(.//div[contains(@class, 'ob-card-list--is-dismissed')])]"
    discard_selected_job_css: str = ".jobs-search-results-list__list-item--active div.job-card-list__dismiss > button"
    selected_job_css: str = ".jobs-search-results-list__list-item--active"
    job_card_title_css: str = ".job-card-list__title"
    discarded_job_card_css = ".job-card-list--is-dismissed"
    selected_job_card_title_css: str = selected_job_css + " " + job_card_title_css
    # job

