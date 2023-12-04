# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

from tempfile import TemporaryDirectory

from housing_pricer.scraping.data_manager import DataManager

TEST_ENDPOINT = "http://example.com"


def test_append_and_load():
    with TemporaryDirectory() as base_dir:
        test_data = {
            "key1": "value1",
            "key2": 300,
            "key3": None,
        }

        data_manager = DataManager(base_dir=base_dir)
        with data_manager:
            data_manager.append_data_to_file(test_data)

        loaded_data = list(data_manager.load_data())[0]

        assert test_data == loaded_data


def test_non_exit_exception_in_context_handler_case():
    # pylint: disable=broad-exception-caught
    # pylint: disable=broad-exception-raised
    with TemporaryDirectory() as base_dir:
        test_data = {"test_key": "test_value"}
        try:
            with DataManager(base_dir) as data_manager:
                data_manager.append_data_to_file(test_data)
                data_manager.mark_endpoint_scraped(TEST_ENDPOINT)
                raise Exception
        except Exception:
            pass

        assert DataManager(base_dir).is_endpoint_scraped(TEST_ENDPOINT)


def test_keyboard_interrupt_in_context_handler_case():
    with TemporaryDirectory() as base_dir:
        test_data = {"test_key": "test_value"}

        try:
            with DataManager(base_dir) as data_manager:
                data_manager.append_data_to_file(test_data)
                data_manager.mark_endpoint_scraped(TEST_ENDPOINT)
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass

        assert DataManager(base_dir).is_endpoint_scraped(TEST_ENDPOINT)
