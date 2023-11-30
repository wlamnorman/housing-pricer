"""Scraper class to handle website interactions."""
# pylint: disable=too-few-public-methods
import requests

from pyrate_limiter import Duration, Rate
from pyrate_limiter.limiter import Limiter
from requests.exceptions import HTTPError, JSONDecodeError, RequestException

class ScrapeError(Exception):
    """
    Raise when an error occurs while interacting with website.

    Attributes
    ----------
    call
        The call that caused the error.
    response
        The HTTP response object returned by the call.
    """

    def __init__(
        self,
        msg: str | None = None,
        call: str | None = None,
        response: requests.Response | None = None,
    ):
        """Initialize AtlasError with optional message, call, and response."""
        super().__init__(msg)
        self.call = call
        self.response = response


class Scraper:
    """Provides methods for querying webpages with rate limiting."""

    def __init__(self, base_url: str, file_path: str, max_requests_per_minute: int = 20):
        """Initialize a scraper with rate limiting.

        Parameters
        ----------
        base_url
            Base url to scrape from.
        file_path
            Path for data storage.
        max_requests_per_minute
            Max number of requests per minute.
        """
        self._rate_limiter = Limiter(
            Rate(limit=max_requests_per_minute, interval=Duration.MINUTE),
            raise_when_fail=False,
            max_delay=Duration.MINUTE.value,
        )
        self.base_url = base_url
        self._session = requests.Session()

    def get(self, endpoint: str) -> bytes:
        """Scrape contents from url.

        Parameters
        ----------
        endpoint
            Endpoint from which to get content from.
        """
        try:
            self._rate_limiter.try_acquire("get")
            response = self._session.get(f"{self.base_url}{endpoint}")
        except RequestException as exc:
            raise ScrapeError() from exc

        if response.status_code == 204:
            return b""

        try:
            response.raise_for_status()
        except HTTPError as exc:
            raise ScrapeError() from exc
        except JSONDecodeError as exc:
            raise ScrapeError() from exc

        return response.content

