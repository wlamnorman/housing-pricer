# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from housing_pricer.scraping.sdk.data_manager import DataManager
from housing_pricer.scraping.sdk.scraper import AlreadyScrapedError, Scraper

MOCK_URL = "https://example.com"
MOCK_ENDPOINT = "/test-endpoint/1337"


def test_scraper_initialization():
    """
    Ensure that Scraper is correctly initialized.
    """
    with TemporaryDirectory() as temp_dir:
        scraper = Scraper(MOCK_URL, DataManager(temp_dir), 30, 10)
        assert scraper.base_url == MOCK_URL
        assert isinstance(scraper.data_manager, DataManager)
        assert scraper._session is not None
        assert scraper._rate_limiter is not None


def test_succesful_get():
    """
    Mocks a succesful get and ensures content is return correctly.
    """
    with TemporaryDirectory() as temp_dir:
        scraper = Scraper(
            MOCK_URL, DataManager(temp_dir), max_requests_per_minute=20, max_delay_seconds=20
        )

        with patch("requests.Session.get") as mocked_get:
            mocked_response = MagicMock()
            mocked_response.raise_for_status.return_value = None
            mocked_response.status_code = 200
            mocked_response.content = b"Test Content"
            mocked_get.return_value = mocked_response

            content = scraper.get(MOCK_ENDPOINT)
            assert content == mocked_response.content


@patch("time.sleep", return_value=None)
def test_rate_limiting_and_throttling(mock_sleep):
    """
    Check that if two succesful `.get` are called right
    after one another, the second call is being throttled.
    """
    with TemporaryDirectory() as temp_dir:
        scraper = Scraper(MOCK_URL, DataManager(temp_dir), 1, 10)
        with patch("requests.Session.get") as mocked_get:
            mocked_response = MagicMock()
            mocked_response.status_code = 200
            mocked_get.return_value = mocked_response

            scraper.get(MOCK_ENDPOINT)
            scraper.get(MOCK_ENDPOINT)
            mock_sleep.assert_called()


def test_raises_already_scraped_error():
    """
    Ensure that Scraper raises AlreadyScrapedError.
    """
    with TemporaryDirectory() as temp_dir:
        scraper = Scraper(MOCK_URL, DataManager(temp_dir), 20, 20)

        scraper.data_manager.mark_endpoint_scraped(MOCK_ENDPOINT)
        with pytest.raises(AlreadyScrapedError):
            scraper.get(MOCK_ENDPOINT)
