"""
Defines the DataManager class for handling storing and loading of data.
"""

import gzip
import hashlib
import json
import pickle
import signal
from pathlib import Path
from typing import Any, Iterable


class DelayedKeyboardInterrupt:
    """
    Context manager for handling keyboard interrupts.

    Ensures that keyboard interrupts can be delayed until a block of code is safely executed.
    """

    def __init__(self):
        self.signal_received = False
        self.old_handler = None

    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.signal(signal.SIGINT, self._handler)

    def _handler(self, sig, frame):
        self.signal_received = (sig, frame)

    def __exit__(self, _type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)  # type: ignore


class DataManager:
    """
    Manager for saving and loading data in an efficient way.

    This class provides methods for saving any Python object to a file
    and for loading objects back from the file. It uses `pickle` for
    serialization/deserialization and `gzip` for compression.
    """

    def __init__(self, base_dir: str, hash_file: str = "endpoint_hashes.json"):
        """
        Initialize the DataManager with a specified base directory.

        Parameters
        ----------
        base_dir
            The base directory path as a string where data files will be
            saved and loaded from.
        hash_file
            The name of the file to store hashes of scraped endpoints. The
            hashes ensure we don't scrape the same endpoint multiple times.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.hash_file = self.base_dir / hash_file
        self.scraped_endpoints = self._load_scraped_endpoints()

    def _load_scraped_endpoints(self):
        """
        Load the set of scraped endpoint hashes from the hash file.
        """

        if self.hash_file.exists():
            with open(self.hash_file, "r", encoding="utf-8") as file_path:
                return set(json.load(file_path))
        return set()

    def _save_scraped_endpoints(self):
        """
        This method writes the set of endpoint hashes to the hash file
        in JSON format. It ensures that the state of scraped endpoints
        is persisted across sessions.
        """
        with open(self.hash_file, "w", encoding="utf-8") as file_path:
            with DelayedKeyboardInterrupt():
                json.dump(list(self.scraped_endpoints), file_path)

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
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()
        return endpoint_hash in self.scraped_endpoints

    def mark_endpoint_scraped(self, endpoint: str):
        """
        Mark an endpoint as scraped by adding its hash to the set.

        This method calculates the hash of the given endpoint and adds
        it to the set of scraped endpoints, then saves the updated set
        to the hash file.

        Parameters
        ----------
        endpoint
            The endpoint URL to mark as scraped.
        """
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()
        self.scraped_endpoints.add(endpoint_hash)
        self._save_scraped_endpoints()

    def _get_file_path(self, file_name: str) -> Path:
        """
        Generate the full file path for a given file name.

        Parameters
        ----------
        file_name
            The name of the file.

        Returns
        -------
            The complete file Path, ensuring it ends with '.gz'.
        """
        if not file_name.endswith(".gz"):
            file_name += ".gz"
        return self.base_dir / file_name

    def append_data_to_file(self, file_name: str, data: Any):
        """
        Append data to a gzip compressed file.

        This method serializes the given data using `pickle` and appends
        it to a gzip compressed file. If the file does not exist, it is
        created.

        Parameters
        ----------
        file_name
            The name of the file to append data to.
        data
            The data to be saved. Can be any serializable Python object.
        """
        file_path = self._get_file_path(file_name)
        with gzip.open(file_path, "ab") as gz_file:
            with DelayedKeyboardInterrupt():
                pickle.dump(data, gz_file)

    def load_data(self, file_name: str) -> Iterable[Any]:
        """
        Load and yield data from a gzip compressed file.

        This method deserializes and yields data from a gzip compressed
        file. It handles file reading and data deserialization errors.

        Parameters
        ----------
        file_name
            The name of the file from which to load the data.

        Yields
        ------
            Yields deserialized data objects from the file.
        """
        file_path = self._get_file_path(file_name)
        with gzip.open(file_path, "rb") as gz_file:
            while True:
                try:
                    yield pickle.load(gz_file)
                except EOFError:
                    break
