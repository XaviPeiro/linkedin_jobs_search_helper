from enum import Enum, IntEnum
from urllib.parse import urlparse, urlunparse, urlencode
from urllib.parse import urlunsplit

from plum import dispatch

# (scheme='http', netloc='www.cwi.nl:80', path='/%7Eguido/Python.html', params='', query='', fragment='')
# urlunparse(("https", "www.linkedin.com", "/jobs/search/", "", {"location": 12312, }, ""))


class LocationCodes(Enum):
    USA: str = "103644278"
    EU: str = "91000000"
    SWTZ: str = "106693272"
    IL: str = "101620260"
    UK: str = "3702942170"
    PL: str = "105072130"


class RemoteCodes(Enum):
    IN_SITE: str = "1"
    REMOTE: str = "2"
    HYBRID: str = "3"


class SalaryCodes(Enum):
    # It defines the minimum salary. EG
    X0K: str = ""
    X40K: str = "1"
    X60K: str = "2"
    X80K: str = "3"
    X100K: str = "4"
    X120K: str = "5"
    X140K: str = "6"
    X160K: str = "7"
    X180K: str = "8"
    X200K: str = "9"


class UrlGenerator:
    def __init__(self):
        ...

    # TODO: Use JobFilter instead of exposing all those variables? It will more resilient.
    #  start = paging (n_items not pages)
    def generate(
        self,
        search_term: str,
        remote: [RemoteCodes],
        salary: SalaryCodes,
        posted_days_ago: int,
        location: LocationCodes,
        start: int = 0
    ):
        query: str
        query_d: dict
        SCHEME: str = "https"
        NETLOC: str = "www.linkedin.com"
        PATH: str = "/jobs/search/"
        params: str = ""
        fragment: str = ""

        # TODO: from variable
        query_d = (
                self.location(location=location) | self.posted_on(days=posted_days_ago) | self.remote(remote) |
                self.salary(salary) | {"start": start} | {"keywords": search_term}
        )

        query = urlencode(query_d)
        url = urlunparse((SCHEME, NETLOC, PATH, params, query, fragment))

        return url

    def location(self, location: LocationCodes) -> dict[str, str]:
        return {"location": location.value}

    def posted_on(self, days: int) -> dict[str, str]:
        total_seconds: str = str(86400 * days)
        any_time: str = ""
        return {"f_TPR": ("r" + total_seconds) if days > 0 else any_time}

    def remote(self, choices: list[RemoteCodes]) -> dict[str, str]:
        parsed_choices: list[str] = [choice.value for choice in choices]
        return {"f_WT": ",".join(parsed_choices)}

    # As long as I know this only works for the USA and UK. Not such a feature for other countries.
    def salary(self, minimum: SalaryCodes) -> dict[str, str]:
        return {"f_SB2": str(minimum.value)}
