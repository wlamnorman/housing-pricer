"""
Defines the DataManager class for handling storing and loading of data.
"""

from pathlib import Path
import gzip
import pickle
from typing import Any, Iterable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    def _get_file_path(self, file_name: str) -> Path:
        """
        Concatenates base directory and file name to complete file path,
        ensuring the file name ends with '.gz'.
        """
        if not file_name.endswith(".gz"):
            file_name += ".gz"
        return self.base_dir / file_name

    def append_data_to_file(self, file_name: str, data: Any):
        """
        Save data to a gzip compressed file in the base directory by appending.
        Handles errors in file operations and data serialization.

        Parameters
        ----------
        file_name
            The name of the file to save the data to.
        data
            The data to be saved. Can be any Python object.
        """
        file_path = self._get_file_path(file_name)
        try:
            with gzip.open(file_path, "ab") as gz_file:
                pickle.dump(data, gz_file)

        except (OSError, pickle.PicklingError) as exc:
            logger.error("Failed to save-append to %s: %s", file_path, exc)

    def load_data(self, file_name: str) -> Iterable[dict[str, Any]]:
        """
        Load and generate data from a gzip compressed file.
        Handles errors in file operations and data deserialization.

        Parameters
        ----------
        file_name
            The name of the file from which to load the data.

        Yields
        ------
            Yields data objects from the file.
        """
        file_path = self._get_file_path(file_name)
        try:
            with gzip.open(file_path, "rb") as gz_file:
                while True:
                    try:
                        yield pickle.load(gz_file)
                    except EOFError:
                        logger.info("Finished loading data from %s", file_path)
                        break
                    except pickle.UnpicklingError as exc:
                        logger.error("Failed to unpickle data from %s: %s", file_path, exc)
        
        except OSError as exc:
            logger.error("Failed to open file %s: %s", file_path, exc)
