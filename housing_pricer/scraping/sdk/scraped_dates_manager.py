"""
Defines the class ScrapedDatesManager to which can determine which dates should be scraped.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from housing_pricer.scraping.sdk.delayed_keyboard_interrupt import DelayedKeyboardInterrupt


class ScrapedDatesManager:
    """
    Class to handle dates to be scraped automatically.
    """

    def __init__(self, base_dir: str, filename: str = "_scraped_dates.txt"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = self._base_dir / filename
        self.scraped_dates = self.load_scraped_dates_from_file()

        # pylint: disable=consider-using-with
        self._file_handle = open(self.file_path, "a", encoding="utf-8")

    def __del__(self):
        """
        Destructor that closes the file handle as instance is garbage collected.
        """
        with self._file_handle as f_handle:
            f_handle.close()

    def load_scraped_dates_from_file(self) -> set[str]:
        """
        Loads scraped dates from file into memory.
        """
        scraped_dates = set()
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as file:
                for date in file.read().splitlines():
                    if date:
                        scraped_dates.add(date)
        return scraped_dates

    def mark_date_scraped(self, date: str):
        """
        Appends `date` to file.
        """
        self.scraped_dates.add(date)
        with DelayedKeyboardInterrupt():
            self._file_handle.write("\n" + date)

    def is_date_scraped(self, date: str) -> bool:
        """
        `True` if date is in scrated_dates else `False`.
        """
        return date in self.scraped_dates

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
