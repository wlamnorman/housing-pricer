# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
from housing_pricer.scraping.data_manager import DataManager


def test_data_manager():
    data_manager = DataManager("test_data")
    test_data = {
        "key1": "value1",
        "key2": 300,
        "key3": None,
    }
    file_name = "test.gz"

    data_manager.append_data_to_file(file_name, test_data)
    loaded_data = list(data_manager.load_data(file_name))[0]
    
    # delete created file after loading but before assert
    test_file_path = data_manager.base_dir / file_name
    if test_file_path.exists():
        test_file_path.unlink()

    assert test_data == loaded_data