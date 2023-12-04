# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from housing_pricer.scraping.data_manager import DataManager
from housing_pricer.scraping.scraper import AlreadyScrapedError, Scraper


def test_duplicate_endpoint_scraping():
    base_url = "https://example.com"
    endpoint = "/test-endpoint"

    with TemporaryDirectory() as temp_dir:
        scraper = Scraper(
            base_url, DataManager(temp_dir), max_requests_per_minute=20, max_delay_seconds=20
        )

        with patch("requests.Session.get") as mocked_get:
            mocked_response = MagicMock()
            mocked_response.raise_for_status.return_value = None
            mocked_response.status_code = 200
            mocked_response.content = b"Test Content"
            mocked_get.return_value = mocked_response

            content = scraper.get(endpoint, mark_endpoint=True)
            assert content == mocked_response.content, "Content mismatch on first scrape"

            with pytest.raises(AlreadyScrapedError):
                scraper.get(endpoint, mark_endpoint=True)
