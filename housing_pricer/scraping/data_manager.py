"""
Defines the DataManager class for handling storing and loading of data.
"""

import gzip
import json
import pickle
from pathlib import Path
from typing import Any, Iterable

from housing_pricer.scraping._data_manager_utils import DelayedKeyboardInterrupt, as_hash


class DataManager:
    """
    A class for efficiently saving and loading data to and from files.

    DataManager is designed to be used as a context manager when saving data, ensuring
    proper opening and closing of the file as well as the safe storage of endpoint hashes.
    When loading data, it does not need to be used as a context manager; data can be
    directly read from the file using the `load_data` method.

    The class utilizes `pickle` for serialization/deserialization and `gzip` for
    compression, handling both binary and text data.
    """

    def __init__(
        self,
        base_dir: str,
        data_filename: str = "scraped_data.gz",
        hash_filename: str = "_scraped_endpoint_hashes.json",
    ):
        """
        Initialize the DataManager with a specified base directory.

        Parameters
        ----------
        base_dir
            The base directory path as a string where data files will be
            saved and loaded from.
        data_filename
            The name of the file to store scraped data in.
        hash_filename
            The name of the file to store hashes of scraped endpoints. The
            hashes ensure we don't scrape the same endpoint multiple times.
        """

        def load_scraped_endpoints(hash_file_path: Path) -> set[str]:
            if hash_file_path.exists():
                with open(hash_file_path, "r", encoding="utf-8") as file_path:
                    return set(json.load(file_path))
            return set()

        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._data_file_path = self._base_dir / data_filename
        self._data_file_handle = None
        self._hash_file_path = self._base_dir / hash_filename
        self._scraped_endpoints = load_scraped_endpoints(self._hash_file_path)

    def __enter__(self):
        """
        Context manager entry method for DataManager.

        Opens the data file for appending and returns the DataManager instance. This method
        should be used when planning to save or append data to the file to ensure proper
        resource management.

        Returns
        -------
            The instance of DataManager.
        """
        self._data_file_handle = gzip.open(self._data_file_path, "ab")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method for DataManager.

        Saves scraped endpoint hashes to the hash file and closes the data file handle.
        This method ensures that all operations within the context are finalized before
        closing the file, even in the case of exceptions.
        """

        def save_scraped_endpoints(hash_file_path: Path, scraped_endpoints: set[str]):
            with open(hash_file_path, "w", encoding="utf-8") as file_path:
                with DelayedKeyboardInterrupt():
                    json.dump(list(scraped_endpoints), file_path)

        save_scraped_endpoints(self._hash_file_path, self._scraped_endpoints)

        assert self._data_file_handle is not None
        self._data_file_handle.close()

    def append_data_to_file(self, data: Any):
        """
        Append data to a gzip compressed file.

        This method serializes the given data using `pickle` and appends
        it to a gzip compressed file. If the file does not exist, it is
        created.

        Parameters
        ----------
        data
            The data to be saved. Can be any serializable Python object.
        """
        assert self._data_file_handle is not None
        with DelayedKeyboardInterrupt():
            pickle.dump(data, self._data_file_handle)

    def load_data(self) -> Iterable[Any]:
        """
        Load and yield data from a gzip compressed file.

        This method can be called directly without the need for a context manager. It
        opens the file for reading, deserializes, and yields data from a gzip compressed
        file.

        Yields
        ------
            Yields deserialized data objects from the file.
        """
        with gzip.open(self._data_file_path, "rb") as gz_file:
            while True:
                try:
                    yield pickle.load(gz_file)
                except EOFError:
                    break

    def mark_endpoint_scraped(self, endpoint: str):
        """
        Mark an endpoint as scraped by adding its hash to the set.

        Parameters
        ----------
        endpoint
            The endpoint URL to mark as scraped.
        """
        endpoint_hash = as_hash(endpoint)
        self._scraped_endpoints.add(endpoint_hash)

    def is_endpoint_scraped(self, endpoint: str) -> bool:
        """
        Checks if an endpoint has already been scraped.

        Parameters
        ----------
        endpoint
            The endpoint URL to check.

        Returns
        -------
            True if the endpoint has already been scraped, False otherwise.
        """
        return as_hash(endpoint) in self._scraped_endpoints
