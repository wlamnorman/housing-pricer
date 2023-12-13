"""
Defines the DataManager class for handling storing and loading of data, and keeping
track of data source.
"""
import json
import logging
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
        self._load_scraped_endpoints()
        self._data_file_handle = open(self._data_file_path, "a", encoding="utf-8")
        return self

    def _load_scraped_endpoints(self):
        """
        Loads already scraped endpoints to avoid re-scraping.
        """
        if self._data_file_path.exists():
            for entry in tqdm(self.load_data(), desc="Loading already scraped endpoints..."):
                self._scraped_endpoints.add(entry["id"])

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method for DataManager which ensures that the file
        handle is closed when exiting context.
        """
        assert self._data_file_handle is not None
        self._data_file_handle.close()

    def append_data_to_file(self, endpoint_id: str | int, data: dict[str, Any]):
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
            entry = {"id": endpoint_id, "data": data}
            json_data = json.dumps(entry)
            self._data_file_handle.write(json_data + "\n")

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

    def mark_endpoint_scraped(self, endpoint_id: str):
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
