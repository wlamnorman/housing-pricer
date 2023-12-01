"""
Defines the DataManager class for handling storing and loading of data.
"""

from pathlib import Path
import gzip
import pickle
from typing import Any, Iterable
import logging


class DataManager:
    """
    Manager for saving and loading data in an efficient way.

    This class provides methods for saving any Python object to a file
    and for loading objects back from the file. It uses `pickle` for
    serialization/deserialization and `gzip` for compression.
    """

    def __init__(self, base_dir: str):
        """
        Initialize the DataManager with a specified base directory.

        Parameters
        ----------
        base_dir
            The base directory path as a string where data files will be
            saved and loaded from.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO)

    def _get_file_path(self, file_name: str) -> Path:
        """Concatenates base directory and file name to complete file path."""
        return self.base_dir / file_name

    def save_data(self, file_name: str, data: Any):
        """
        Save data to a gzip compressed file in the base directory.

        Parameters
        ----------
        file_name
            The name of the file to save the data to.
        data
            The data to be saved. Can be any Python object, USE WITH CAUTION.
        """
        file_path = self._get_file_path(file_name)
        with gzip.open(file_path, "ab") as gz_file:
            pickle.dump(data, gz_file)

    def load_data(self, file_name: str) -> Iterable[dict[str, Any]]:
        """
        Load and generate data from a gzip compressed file.

        Parameters
        ----------
        file_name
            The name of the file from which to load the data.

        Yields
        ------
            Yields data objects from the file.
        """
        file_path = self._get_file_path(file_name)
        with gzip.open(file_path, "rb") as gz_file:
            while True:
                try:
                    yield pickle.load(gz_file)
                except EOFError:
                    break
