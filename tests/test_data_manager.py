# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

from tempfile import TemporaryDirectory

from housing_pricer.scraping.sdk.data_manager import DataManager

MOCK_ENDPOINT = "http://example.com"
MOCK_DATA = {
    "key1": "value1",
    "key2": 300,
    "key3": None,
}
MOCK_ENDPOINT_ID = "bostad/1337"
MOCK_DATE = "2023-01-01"
MOCK_ENTRY = {"id": MOCK_ENDPOINT_ID, "date": MOCK_DATE, "data": MOCK_DATA}


def test_append_and_load():
    with TemporaryDirectory() as base_dir:
        data_manager = DataManager(base_dir=base_dir)
        with data_manager:
            data_manager.append_data_to_file(
                endpoint_id=MOCK_ENDPOINT_ID, date=MOCK_DATE, data=MOCK_DATA
            )

        loaded_entry = list(data_manager.load_data())[0]
        assert MOCK_ENTRY == loaded_entry


def test_mark_and_is_endpoint_scraped():
    with TemporaryDirectory() as base_dir:
        with DataManager(base_dir) as data_manager:
            data_manager._mark_endpoint_scraped(MOCK_ENDPOINT_ID)
            assert data_manager.is_endpoint_scraped(MOCK_ENDPOINT_ID)


def test_append_marks_endpoint_id():
    with TemporaryDirectory() as base_dir:
        data_manager = DataManager(base_dir=base_dir)
        with data_manager:
            data_manager.append_data_to_file(
                endpoint_id=MOCK_ENDPOINT_ID, date=MOCK_DATE, data=MOCK_DATA
            )
        assert data_manager.is_endpoint_scraped(MOCK_ENDPOINT_ID)


def test_append_marks_endpoint_id_and_loads_properly():
    with TemporaryDirectory() as base_dir:
        with DataManager(base_dir=base_dir) as data_manager:
            data_manager.append_data_to_file(
                endpoint_id=MOCK_ENDPOINT_ID, date=MOCK_DATE, data=MOCK_DATA
            )
        with DataManager(base_dir=base_dir) as data_manager:
            assert data_manager.is_endpoint_scraped(MOCK_ENDPOINT_ID)


def test_non_exit_exception():
    # pylint: disable=broad-exception-caught
    # pylint: disable=broad-exception-raised
    with TemporaryDirectory() as base_dir:
        try:
            with DataManager(base_dir) as data_manager:
                data_manager.append_data_to_file(
                    endpoint_id=MOCK_ENDPOINT_ID, date=MOCK_DATE, data=MOCK_DATA
                )
                raise Exception
        except Exception:
            pass

        with DataManager(base_dir) as data_manager:
            loaded_entry = list(data_manager.load_data())[0]
            assert loaded_entry == MOCK_ENTRY, "non-exit Exception breaks data loading"
            assert data_manager.is_endpoint_scraped(
                MOCK_ENDPOINT_ID
            ), "non-exit Exception breaks scraped endpoint tracking"


def test_keyboard_interrupt_in_context_handler_case():
    with TemporaryDirectory() as base_dir:
        try:
            with DataManager(base_dir) as data_manager:
                data_manager.append_data_to_file(
                    endpoint_id=MOCK_ENDPOINT_ID, date=MOCK_DATE, data=MOCK_DATA
                )
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass

        with DataManager(base_dir) as data_manager:
            loaded_entry = list(data_manager.load_data())[0]
            assert loaded_entry == MOCK_ENTRY, "KeyboardInterrupt breaks data loading"
            assert data_manager.is_endpoint_scraped(
                MOCK_ENDPOINT_ID
            ), "KeyboardInterrupt breaks scraped endpoint tracking"


TODAY: str = "2023-12-05"
BACK_TO_DATE: str = "2023-12-01"
VIABLE_DAYS = {"2023-12-04", "2023-12-03", "2023-12-02", BACK_TO_DATE}


class TestDatesFunctionality:
    def test_dates_to_scrape_with_no_dates_scraped(self):
        with TemporaryDirectory() as base_dir:
            with DataManager(base_dir) as data_manager:
                assert (
                    set(data_manager._get_dates_to_scrape(BACK_TO_DATE, _today=TODAY))
                    == VIABLE_DAYS
                )

    def test_dates_to_scrape_with_dates_scraped(self):
        for date_marked_as_scraped in VIABLE_DAYS:
            with TemporaryDirectory() as base_dir:
                with DataManager(base_dir) as data_manager:
                    data_manager._mark_date_scraped(date_marked_as_scraped)
                    dates_to_scrape = set(
                        data_manager._get_dates_to_scrape(BACK_TO_DATE, _today=TODAY)
                    )
                    assert dates_to_scrape == VIABLE_DAYS

    def test_marked_dates_by_adding_scraped_dates_sequentially(self):
        expected_dates = set()
        with TemporaryDirectory() as base_dir:
            with DataManager(base_dir) as data_manager:
                for date_marked_as_scraped in VIABLE_DAYS:
                    expected_dates.add(date_marked_as_scraped)
                    data_manager._mark_date_scraped(date_marked_as_scraped)
                    assert data_manager._scraped_dates == expected_dates

    def test_dates_to_scrape_by_entering_context_with_multiple_scraped_dates(self):
        scraped_entries = [
            {"endpoint_id": 0, "date": "2023-12-04", "data": None},
            {"endpoint_id": 1, "date": "2023-12-03", "data": None},
            {"endpoint_id": 2, "date": "2023-12-02", "data": None},
        ]
        expected_dates_to_scrape = {"2023-12-04", "2023-12-02", "2023-12-01"}
        with TemporaryDirectory() as base_dir:
            with DataManager(base_dir) as data_manager:
                for entry in scraped_entries:
                    data_manager.append_data_to_file(**entry)

            with DataManager(base_dir) as data_manager:
                dates_to_scrape = set(
                    data_manager._get_dates_to_scrape(back_to_date=BACK_TO_DATE, _today=TODAY)
                )
                assert dates_to_scrape == expected_dates_to_scrape

                loaded_dates_to_scrape = set(data_manager.dates_to_scrape)
                for date in expected_dates_to_scrape:
                    assert date in loaded_dates_to_scrape
