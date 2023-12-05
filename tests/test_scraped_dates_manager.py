# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

import os
from tempfile import TemporaryDirectory

from housing_pricer.scraping.scraped_dates_manager import ScrapedDatesManager

TODAY: str = "2023-12-05"
BACK_TO_DATE: str = "2023-12-01"
VIABLE_DAYS = {"2023-12-04", "2023-12-03", "2023-12-02", BACK_TO_DATE}


class TestBasicFuntionality:
    def test_mark_date_scraped_and_is_scraped(self):
        test_date_to_mark_and_check = "2023-12-02"

        with TemporaryDirectory() as temp_dir:
            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
                scraped_dates_manager.mark_date_scraped(test_date_to_mark_and_check)
                assert scraped_dates_manager.is_date_scraped(test_date_to_mark_and_check)

    def test_dates_to_scrape_with_no_dates_scraped(self):
        with TemporaryDirectory() as temp_dir:
            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                dates_to_scrape = set(
                    scraped_dates_manager.dates_to_scrape(BACK_TO_DATE, _today=TODAY)
                )
                expected_dates = VIABLE_DAYS
                assert dates_to_scrape == expected_dates

    def test_dates_to_scrape_with_dates_scraped(self):
        for date_marked_as_scraped in VIABLE_DAYS:
            with TemporaryDirectory() as temp_dir:
                with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                    scraped_dates_manager.mark_date_scraped(date_marked_as_scraped)
                    dates_to_scrape = set(
                        scraped_dates_manager.dates_to_scrape(BACK_TO_DATE, _today=TODAY)
                    )
                    expected_dates = VIABLE_DAYS.copy()
                    expected_dates.remove(date_marked_as_scraped)
                    assert dates_to_scrape == expected_dates

    def test_adding_scraped_dates_sequentially(self):
        expected_dates = {}
        with TemporaryDirectory() as temp_dir:
            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                for date_marked_as_scraped in VIABLE_DAYS:
                    expected_dates[date_marked_as_scraped] = True
                    scraped_dates_manager.mark_date_scraped(date_marked_as_scraped)
                    assert scraped_dates_manager.scraped_dates == expected_dates


class TestFileFunctionality:
    def test_loading_scraped_dates_from_file(self):
        with TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "_scraped_dates.txt")
            with open(file_path, "w", encoding="utf-8") as file:
                for date in VIABLE_DAYS:
                    file.write(date + "\n")

            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                for date in VIABLE_DAYS:
                    assert scraped_dates_manager.is_date_scraped(date)

    def test_saving_scraped_dates_to_file(self):
        with TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "_scraped_dates.txt")
            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                for date in VIABLE_DAYS:
                    scraped_dates_manager.mark_date_scraped(date)

            with open(file_path, "r", encoding="utf-8") as file:
                saved_dates = file.read().splitlines()
                assert set(saved_dates) == set(VIABLE_DAYS)

    def test_saving_and_loading_from_file(self):
        with TemporaryDirectory() as temp_dir:
            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                for date in VIABLE_DAYS:
                    scraped_dates_manager.mark_date_scraped(date)

            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                # pylint: disable=protected-access
                scraped_dates_manager._load_scraped_dates_from_file()
                expected_scarped_dates = {date: True for date in VIABLE_DAYS}
                assert scraped_dates_manager.scraped_dates == expected_scarped_dates

    def test_handling_empty_file(self):
        with TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "_scraped_dates.txt")
            with open(file_path, "a", encoding="utf-8") as f_handle:
                f_handle.close()

            with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                assert not scraped_dates_manager.scraped_dates


class TestExceptionHandling:
    def test_non_exit_exception_handling(self):
        # pylint: disable=broad-exception-caught
        # pylint: disable=broad-exception-raised
        with TemporaryDirectory() as temp_dir:
            try:
                with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                    for date in VIABLE_DAYS:
                        scraped_dates_manager.mark_date_scraped(date)
                    raise Exception
            except Exception:
                pass

            with ScrapedDatesManager(base_dir=temp_dir) as new_manager:
                for date in VIABLE_DAYS:
                    assert new_manager.is_date_scraped(date)

    def test_keyboard_interrupt_handling(self):
        with TemporaryDirectory() as temp_dir:
            try:
                with ScrapedDatesManager(base_dir=temp_dir) as scraped_dates_manager:
                    for date in VIABLE_DAYS:
                        scraped_dates_manager.mark_date_scraped(date)
                    raise KeyboardInterrupt
            except KeyboardInterrupt:
                pass

            with ScrapedDatesManager(base_dir=temp_dir) as new_manager:
                for date in VIABLE_DAYS:
                    assert new_manager.is_date_scraped(date)
