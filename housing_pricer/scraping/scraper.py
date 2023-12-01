"""
Scraper class to handle website interactions. Includes rate limiting,
informative error propagation, logging, re-try logic for requests and
data management through a DataManager.
"""
import logging

# pylint: disable=too-few-public-methods
import time

import requests
from pyrate_limiter import Duration, Rate
from pyrate_limiter.limiter import Limiter
from requests.exceptions import HTTPError, RequestException

from housing_pricer.scraping.data_manager import DataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        msg: str | None = None,
        call: str | None = None,
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

    def __init__(self, base_url: str, data_manager: DataManager, max_requests_per_minute: int = 20):
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
        """
        self.base_url = base_url
        self._session = requests.Session()
        self._rate_limiter = Limiter(
            Rate(limit=max_requests_per_minute, interval=Duration.MINUTE),
            raise_when_fail=False,
            max_delay=Duration.MINUTE.value,
        )
        self._data_manager = data_manager

    def _try_get_except(self, endpoint: str) -> bytes:
        """
        Scrape content from url.

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
                logger.info("Received 204 No content for %s", endpoint)
                return b""
            return response.content

        except (HTTPError, RequestException) as exc:
            raise ScrapeError() from exc

    def get(
        self, endpoint: str, mark_endpoint: bool, retries: int = 2, seconds_delay: int = 1
    ) -> bytes:
        """
        Scrape content from url with retry logic unless already scraped.

        Parameters
        ----------
        endpoint
            Endpoint from which to get content from.
        mark_endpoint
            If endpoint should be marked as scraped in the DataManager (intended
            to be used for when information is retrieved, not for searches).
        retries
            Number of retry attempts.
        delay
            Delay between retries in seconds.
        """
        if self._data_manager.is_endpoint_scraped(endpoint):
            logger.info("%s already scraped", endpoint)
            raise AlreadyScrapedError(f"{endpoint} already scraped")

        for _ in range(retries):
            try:
                content = self._try_get_except(endpoint)
                if mark_endpoint:
                    self._data_manager.mark_endpoint_scraped(endpoint)
                return content

            except ScrapeError as exc:
                logger.error("%s, retrying in %d seconds...", exc, seconds_delay)
                time.sleep(secs=seconds_delay)

        logger.info("Failed to retrieve data from %s after %s attempts.", endpoint, retries)
        return b""
