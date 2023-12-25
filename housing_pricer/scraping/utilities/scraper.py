"""
Scraper class to handle website interactions. Includes rate limiting,
informative error propagation, re-try logic for requests, throttling,
and data management using a DataManager.
"""
# pylint: disable=too-few-public-methods
import logging
import time

import requests
from pyrate_limiter import Duration, Rate
from pyrate_limiter.limiter import Limiter
from requests.exceptions import HTTPError, RequestException

from housing_pricer.scraping.utilities.data_manager import DataManager

# configure pyrate loggers level from INFO to WARNING
# this removes pyrates logger to message about enforcing
# restrictions to respect the rate limiter
pyrate_logger = logging.getLogger("pyrate_limiter")
pyrate_logger.setLevel(logging.WARNING)


class ScrapeError(Exception):
    """
    For capturing more detailed errors that occur while interacting with websites.

    Attributes
    ----------
    call
        The call that caused the error.
    response
        The HTTP response object returned by the call.
    """

    def __init__(
        self,
        msg: str,
        call: str,
        response: requests.Response | None = None,
    ):
        """
        Initialize ScrapeError with optional message, call, and response.
        """
        super().__init__(msg)
        self.call = call
        self.response = response


class AlreadyScrapedError(Exception):
    """Exception raised when an endpoint has already been scraped."""


class Scraper:
    """Provides methods for scraping webpages."""

    def __init__(
        self,
        base_url: str,
        data_manager: DataManager,
        max_requests_per_minute: int,
        max_delay_seconds: int,
    ):
        """
        Initialize a scraper with rate limiting and associated DataManager.

        Parameters
        ----------
        base_url
            Base url to scrape from.
        data_manager
            DataManager instance for tracking scraped data and saving data.
        max_requests_per_minute
            Max number of requests per minute.
        max_delay_seconds
            Max delay if max request per minute is exceeded.
        """
        self.base_url = base_url
        self._session = requests.Session()
        self._rate_limiter = Limiter(
            Rate(limit=max_requests_per_minute, interval=Duration.MINUTE),
            raise_when_fail=False,
            max_delay=Duration.SECOND.value * max_delay_seconds,
        )
        self.data_manager = data_manager
        self._last_request_time = None
        self._request_interval = 60 / max_requests_per_minute

    def get(self, endpoint: str, tries: int = 2) -> bytes:
        """
        Scrape content from url with retry logic unless already scraped.

        Parameters
        ----------
        endpoint
            Endpoint from which to get content from.
        tries
            Number of request attempts.
        """
        if self.data_manager.is_endpoint_scraped(endpoint):
            raise AlreadyScrapedError(f"{endpoint} already scraped; skipping")

        for attempt in range(tries):
            self._throttle_requests()
            try:
                content = self._try_get_except(endpoint)
                return content

            except ScrapeError:
                if attempt == tries - 1:
                    raise

        raise RuntimeError("Failed to scrape content, but no ScrapeError was captured.")

    def _try_get_except(self, endpoint: str) -> bytes:
        """
        Tries to get content; raises ScrapeError if something goes wrong.

        Parameters
        ----------
        endpoint
            Endpoint from which to get content from.
        """
        try:
            # check if request would exceed rate limit; if so delay
            self._rate_limiter.try_acquire("get")

            response = self._session.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()

            if response.status_code == 204:
                return b""
            return response.content

        except (HTTPError, RequestException) as exc:
            requested_url = f"{self.base_url}{endpoint}"
            raise ScrapeError(msg=str(exc), call=requested_url) from exc

    def _throttle_requests(self):
        """
        Enforces a delay between requests to adhere to the rate limit.
        """
        if self._last_request_time is not None:
            elapsed_time = time.time() - self._last_request_time
            wait_time = self._request_interval - elapsed_time
            if wait_time > 0:
                time.sleep(wait_time)
        self._last_request_time = time.time()
