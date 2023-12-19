"""
Defines the DataManager class for handling storing and loading of data, and keeping
track of data source.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from tqdm import tqdm

from housing_pricer.scraping.sdk.delayed_keyboard_interrupt import DelayedKeyboardInterrupt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManager:
    """
    DataManager is designed to be used as a context manager when saving data, ensuring
    proper opening and closing of the file.

    When loading data, it does not need to be used as a context manager; data can be
    yielded from the file using the `load_data` method.
    """

    def __init__(
        self,
        base_dir: str,
        data_filename: str = "scraped_data",
    ):
        """
        Initialize the DataManager with a specified base directory and data file.

        Parameters
        ----------
        base_dir
            The base directory path as a string where data files will be
            saved and loaded from.
        data_filename
            The name of the JSON file to store scraped data in.
        """
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._data_file_path = self._base_dir / f"{data_filename}.json"
        self._data_file_handle = None
        self._scraped_endpoints = set()
        self._scraped_dates = set()
        self.dates_to_scrape: Iterable[str]

    def __enter__(self):
        """
        Context manager entry method for DataManager.

        Opens the data file for appending and returns the DataManager instance. This method
        should be used when planning to save or append data to the file to ensure proper
        resource management.

        The entry method also loads already scraped endpoints to avoid unnecessary
        re-scraping of endpoints.

        Returns
        -------
            The instance of DataManager.
        """
        self._load_scraped_endpoints_and_dates()
        self.dates_to_scrape = self._get_dates_to_scrape()
        self._data_file_handle = open(self._data_file_path, "a", encoding="utf-8")
        return self

    def _load_scraped_endpoints_and_dates(self):
        """
        Loads already scraped endpoints and dates to avoid re-scraping.
        """
        if self._data_file_path.exists():
            for entry in tqdm(
                self.load_data(), desc="Loading already scraped endpoints and dates..."
            ):
                self._mark_endpoint_scraped(entry["id"])
                self._mark_date_scraped(entry["date"])

    def _get_dates_to_scrape(
        self, back_to_date: str = "2015-01-01", _today: str | None = None
    ) -> Iterable[str]:
        """
        Returns a list of todays between and including yesterday and `back_to_date`
        which has not yet been scraped.
        NOTE: `_today` should not be give by the user, it exists soley for testing
        purposes.
        """

        def generate_date_range(end_date, start_date) -> Iterable[str]:
            n_days = (end_date - start_date).days + 1
            yield from ((end_date - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(n_days))

        if _today is None:
            yesterday = datetime.today().date() - timedelta(days=1)
        else:
            yesterday = datetime.strptime(_today, "%Y-%m-%d").date() - timedelta(days=1)

        back_to_date_ = datetime.strptime(back_to_date, "%Y-%m-%d").date()

        if not self._scraped_dates:
            yield from generate_date_range(end_date=yesterday, start_date=back_to_date_)
            return

        dates_as_ymd_datetimes = [
            datetime.strptime(date, "%Y-%m-%d") for date in self._scraped_dates
        ]
        latest_scraped_date = max(dates_as_ymd_datetimes).date()
        earliest_scraped_date = min(dates_as_ymd_datetimes).date()

        yield from generate_date_range(end_date=yesterday, start_date=latest_scraped_date)
        yield from generate_date_range(end_date=earliest_scraped_date, start_date=back_to_date_)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method for DataManager which ensures that the file
        handle is closed when exiting context.
        """
        assert self._data_file_handle is not None
        self._data_file_handle.close()

    def append_data_to_file(self, endpoint_id: str | int, date: str, data: dict[str, Any]):
        """
        Append data in JSON format to file.

        Parameters
        ----------
        id
            A unique source identifier for the endpoint from which data was gathered.
        data
            The data to be saved, assumed to be in a format compatible with JSON serialization.
        """
        assert self._data_file_handle is not None
        with DelayedKeyboardInterrupt():
            entry = {"id": endpoint_id, "date": date, "data": data}
            json_data = json.dumps(entry)
            self._data_file_handle.write(json_data + "\n")
            self._mark_endpoint_scraped(endpoint_id)

    def load_data(self) -> Iterable[Any]:
        """
        Load and yield data from file.

        This method can be called directly without the need for a context manager.

        Yields
        ------
            Yields deserialized data objects from the file.
        """
        try:
            with open(self._data_file_path, "r", encoding="utf-8") as data_file:
                for entry in data_file:
                    yield json.loads(entry)
        except EOFError:
            return

    def _mark_date_scraped(self, date: str | int):
        """
        Mark a date as scraped by adding it to the scraped dates set.

        Parameters
        ----------
        date
            The date scraped.
        """
        self._scraped_dates.add(date)

    def _mark_endpoint_scraped(self, endpoint_id: str | int):
        """
        Mark an endpoint as scraped by adding its id to the
        scraped endpoints set.

        Parameters
        ----------
        endpoint_id
            The endpoint identifier to mark as scraped.
        """
        self._scraped_endpoints.add(endpoint_id)

    def is_endpoint_scraped(self, endpoint_id: str) -> bool:
        """
        Checks if an endpoint has already been scraped.

        Parameters
        ----------
        endpoint_id
            The endpoint identifier to check.

        Returns
        -------
            True if the endpoint has already been scraped, False otherwise.
        """
        return endpoint_id in self._scraped_endpoints
