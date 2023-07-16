from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver


def element_exists(chrome: WebDriver, find_arguments: tuple) -> bool:
    try:
        chrome.find_element(*find_arguments)
    except NoSuchElementException:
        return False
    return True
