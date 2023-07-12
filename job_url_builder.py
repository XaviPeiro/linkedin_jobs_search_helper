from enum import Enum, IntEnum
from urllib.parse import urlparse, urlunparse, urlencode
from urllib.parse import urlunsplit

from plum import dispatch

# (scheme='http', netloc='www.cwi.nl:80', path='/%7Eguido/Python.html', params='', query='', fragment='')
# urlunparse(("https", "www.linkedin.com", "/jobs/search/", "", {"location": 12312, }, ""))


class LocationCodes(Enum):
    USA = 103644278


class RemoteCodes(Enum):
    PRESENTIAL: str = "1"
    REMOTE: str = "2"
    HYBRID: str = "3"


class SalaryCodes(IntEnum):
    X40K: int = 1
    X60K: int = 2
    X80K: int = 3
    X100K: int = 4
    X120K: int = 5
    X140K: int = 6
    X160K: int = 7
    X180K: int = 8
    X200K: int = 9


class UrlGenerator:
    def __init__(self):
        ...

    # TODO: Config object od something
    def generate(self, location: str = "", start: int = 0):
        query: str
        query_d: dict
        SCHEME: str = "https"
        NETLOC: str = "www.linkedin.com"
        PATH: str = "/jobs/search/"
        params: str = ""
        fragment: str = ""

        # TODO: from variable
        query_d = (
                self.location(location="USA") | self.posted_on(days=30) | self.remote(["REMOTE"]) |
                self.salary("X80K") | {"start": start}
        )

        query = urlencode(query_d)
        url = urlunparse((SCHEME, NETLOC, PATH, params, query, fragment))

        return url

    def location(self, location: str) -> dict[str, str]:
        return {"location": LocationCodes[location].value}

    def posted_on(self, days: int) -> dict[str, str]:
        total_seconds: str = str(86400 * days)
        any_time: str = ""
        return {"f_TPR": total_seconds if days > 0 else any_time}

    def remote(self, choices: list) -> dict[str, str]:
        parsed_choices: list[str] = [RemoteCodes[choice].value for choice in choices]
        return {"f_WT": ",".join(parsed_choices)}

    # As long as I know this only works for the USA and UK. Not such a feature for other countries.
    def salary(self, minimum: str) -> dict[str, str]:
        return {"f_SB2": str(SalaryCodes[minimum].value)}
