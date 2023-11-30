"""Manager for saving and loading data in an efficient way."""

from pathlib import Path
import gzip
import pickle
from typing import Any, Iterable
import logging


class DataManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO)

    def _get_file_path(self, file_name: str) -> Path:
        return self.base_dir / file_name

    def save_data(self, file_name: str, data: Any):
        file_path = self._get_file_path(file_name)
        with gzip.open(file_path, "ab") as gz_file:
            pickle.dump(data, gz_file)

    def load_data(self, file_name: str) -> Iterable[dict[str, Any]]:
        file_path = self._get_file_path(file_name)
        with gzip.open(file_path, "rb") as gz_file:
            while True:
                try:
                    yield pickle.load(gz_file)
                except EOFError:
                    break
