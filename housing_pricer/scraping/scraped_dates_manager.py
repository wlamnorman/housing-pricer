"""
Defines the class ScrapedDatesManager to which can determine which dates should be scraped.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from housing_pricer.scraping._utils._data_manager_utils import DelayedKeyboardInterrupt


class ScrapedDatesManager:
    """
    Class to handle which dates should be scraped automatically.

    Note: This class has to be used as a context manager.
    """

    def __init__(self, base_dir: str, filename: str = "_scraped_dates.txt"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self._base_dir / filename
        self.scraped_dates = {}

    def __enter__(self):
        """
        Loads scraped dates as we enter context.
        """
        self._load_scraped_dates_from_file()
        return self

    def _load_scraped_dates_from_file(self):
        """
        Loads scraped dates as dict (for hash-ability).
        """
        if self._file_path.exists():
            with open(self._file_path, "r", encoding="utf-8") as file:
                for date in file.read().splitlines():
                    self.scraped_dates[date] = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ensures scraped dates are written to file as context is exited.
        """
        self._save_scraped_dates_to_file()

    def _save_scraped_dates_to_file(self):
        """
        Writes scraped dates to file.
        """
        f_handle = open(self._file_path, "w", encoding="utf-8")
        with DelayedKeyboardInterrupt(), f_handle:
            for date, is_in_scraped_dates in self.scraped_dates.items():
                if is_in_scraped_dates:
                    f_handle.write(date + "\n")

    def mark_date_scraped(self, date: str):
        """
        Adds `date` to dict of scraped dates.
        """
        self.scraped_dates[date] = True

    def is_date_scraped(self, date: str) -> bool:
        """
        `True` if date is in scrated_dates else `False`.
        """
        return self.scraped_dates[date]

    def dates_to_scrape(self, back_to_date: str, _today: str | None = None) -> Iterable[str]:
        """
        Returns a list of todays between yesterday and `back_to_date` which has not yet
        been scraped. NOTE: `_today` should not be give by the user, it exists only for testing
        purposes.
        """

        def generate_date_range(end_date, start_date) -> Iterable[str]:
            n_days = (end_date - start_date).days
            yield from ((end_date - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(n_days))

        if _today is None:
            yesterday = datetime.today().date() - timedelta(days=1)
        else:
            yesterday = datetime.strptime(_today, "%Y-%m-%d").date() - timedelta(days=1)

        back_to_date_ = datetime.strptime(back_to_date, "%Y-%m-%d").date()

        if not self.scraped_dates:
            yield from generate_date_range(yesterday, back_to_date_ - timedelta(days=1))
            return

        latest_scraped_date = max(
            datetime.strptime(date, "%Y-%m-%d") for date in self.scraped_dates
        ).date()
        earliest_scraped_date = min(
            datetime.strptime(date, "%Y-%m-%d") for date in self.scraped_dates
        ).date()

        yield from generate_date_range(yesterday, latest_scraped_date)
        yield from generate_date_range(
            earliest_scraped_date - timedelta(days=1), back_to_date_ - timedelta(days=1)
        )
