# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
import os
import shutil
import unittest
from unittest.mock import MagicMock, patch

from housing_pricer.scraping.data_manager import DataManager
from housing_pricer.scraping.scraper import AlreadyScrapedError, Scraper

TEST_DATA_DIR: str = "test_data"


class TestScraper(unittest.TestCase):
    def setUp(self):
        self.data_manager_dir = TEST_DATA_DIR
        self.endpoint_hash_file = os.path.join(self.data_manager_dir, "endpoint_hashes.json")

        if os.path.exists(self.endpoint_hash_file):
            os.remove(self.endpoint_hash_file)

    def test_duplicate_endpoint_scraping(self):
        base_url = "https://example.com"
        data_manager = DataManager(TEST_DATA_DIR)
        scraper = Scraper(base_url, data_manager)
        endpoint = "/test-endpoint"

        with patch("requests.Session.get") as mocked_get:
            mocked_response = MagicMock()
            mocked_response.raise_for_status.return_value = None
            mocked_response.status_code = 200
            mocked_response.content = b"Test Content"
            mocked_get.return_value = mocked_response

            try:
                content = scraper.get(endpoint, mark_endpoint=True)
                self.assertEqual(content, mocked_response.content)
            except AlreadyScrapedError:
                self.fail("AlreadyScrapedError raised on first scrape")

            with self.assertRaises(AlreadyScrapedError):
                scraper.get(endpoint, mark_endpoint=True)

    def tearDown(self):
        if os.path.exists(self.data_manager_dir):
            shutil.rmtree(self.data_manager_dir)


if __name__ == "__main__":
    unittest.main()
