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
MOCK_ENTRY = {"id": MOCK_ENDPOINT_ID, "data": MOCK_DATA}


def test_append_and_load():
    with TemporaryDirectory() as base_dir:
        data_manager = DataManager(base_dir=base_dir)
        with data_manager:
            data_manager.append_data_to_file(endpoint_id=MOCK_ENDPOINT_ID, data=MOCK_DATA)

        loaded_entry = list(data_manager.load_data())[0]
        assert MOCK_ENTRY == loaded_entry


def test_mark_and_is_endpoint_scraped():
    with TemporaryDirectory() as base_dir:
        with DataManager(base_dir) as data_manager:
            data_manager.mark_endpoint_scraped(MOCK_ENDPOINT_ID)
            assert data_manager.is_endpoint_scraped(MOCK_ENDPOINT_ID)


def test_non_exit_exception():
    # pylint: disable=broad-exception-caught
    # pylint: disable=broad-exception-raised
    with TemporaryDirectory() as base_dir:
        try:
            with DataManager(base_dir) as data_manager:
                data_manager.append_data_to_file(endpoint_id=MOCK_ENDPOINT_ID, data=MOCK_DATA)
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
                data_manager.append_data_to_file(endpoint_id=MOCK_ENDPOINT_ID, data=MOCK_DATA)
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass

        with DataManager(base_dir) as data_manager:
            loaded_entry = list(data_manager.load_data())[0]
            assert loaded_entry == MOCK_ENTRY, "KeyboardInterrupt breaks data loading"
            assert data_manager.is_endpoint_scraped(
                MOCK_ENDPOINT_ID
            ), "KeyboardInterrupt breaks scraped endpoint tracking"
