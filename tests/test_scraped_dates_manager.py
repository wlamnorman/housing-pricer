# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

import os
from tempfile import TemporaryDirectory

from housing_pricer.scraping.sdk.scraped_dates_manager import ScrapedDatesManager

TODAY: str = "2023-12-05"
BACK_TO_DATE: str = "2023-12-01"
VIABLE_DAYS = {"2023-12-04", "2023-12-03", "2023-12-02", BACK_TO_DATE}


class TestBasicFuntionality:
    def test_mark_date_scraped_and_is_scraped(self):
        test_date_to_mark_and_check = "2023-12-02"

        with TemporaryDirectory() as temp_dir:
            scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
            scraped_dates_manager.mark_date_scraped(test_date_to_mark_and_check)
            assert scraped_dates_manager.is_date_scraped(test_date_to_mark_and_check)

    def test_dates_to_scrape_with_no_dates_scraped(self):
        with TemporaryDirectory() as temp_dir:
            scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
            dates_to_scrape = set(scraped_dates_manager.dates_to_scrape(BACK_TO_DATE, _today=TODAY))
            expected_dates = VIABLE_DAYS
            assert dates_to_scrape == expected_dates

    def test_dates_to_scrape_with_dates_scraped(self):
        for date_marked_as_scraped in VIABLE_DAYS:
            with TemporaryDirectory() as temp_dir:
                scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
                scraped_dates_manager.mark_date_scraped(date_marked_as_scraped)
                dates_to_scrape = set(
                    scraped_dates_manager.dates_to_scrape(BACK_TO_DATE, _today=TODAY)
                )
                expected_dates = VIABLE_DAYS.copy()
                expected_dates.remove(date_marked_as_scraped)
                assert dates_to_scrape == expected_dates

    def test_adding_scraped_dates_sequentially(self):
        expected_dates = set()
        with TemporaryDirectory() as temp_dir:
            scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
            for date_marked_as_scraped in VIABLE_DAYS:
                expected_dates.add(date_marked_as_scraped)
                scraped_dates_manager.mark_date_scraped(date_marked_as_scraped)
                assert scraped_dates_manager.scraped_dates == expected_dates


class TestFileFunctionality:
    def test_saving_and_loading_from_file(self):
        with TemporaryDirectory() as temp_dir:
            scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
            for date in VIABLE_DAYS:
                scraped_dates_manager.mark_date_scraped(date)
            del scraped_dates_manager

            scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
            assert scraped_dates_manager.scraped_dates == VIABLE_DAYS

    def test_handling_empty_file(self):
        with TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "_scraped_dates.txt")
            with open(file_path, "a", encoding="utf-8") as f_handle:
                f_handle.close()

            scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
            assert not scraped_dates_manager.scraped_dates


class TestExceptionHandling:
    def test_non_exit_exception_handling(self):
        # pylint: disable=broad-exception-caught
        # pylint: disable=broad-exception-raised
        with TemporaryDirectory() as temp_dir:
            try:
                scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
                for date in VIABLE_DAYS:
                    scraped_dates_manager.mark_date_scraped(date)

                del scraped_dates_manager
                raise Exception
            except Exception:
                pass

            new_manager = ScrapedDatesManager(base_dir=temp_dir)
            for date in VIABLE_DAYS:
                assert new_manager.is_date_scraped(date)

    def test_keyboard_interrupt_handling(self):
        with TemporaryDirectory() as temp_dir:
            try:
                scraped_dates_manager = ScrapedDatesManager(base_dir=temp_dir)
                for date in VIABLE_DAYS:
                    scraped_dates_manager.mark_date_scraped(date)

                del scraped_dates_manager
                raise KeyboardInterrupt
            except KeyboardInterrupt:
                pass

            new_manager = ScrapedDatesManager(base_dir=temp_dir)
            for date in VIABLE_DAYS:
                assert new_manager.is_date_scraped(date)
