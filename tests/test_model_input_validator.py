import pytest
from housing_pricer.valuation_api._utilities.model_input_validator import (
    ModelInputValidator,
)

TRAINING_FEATURE_DOMAIN = {
    "construction_year": {"min": 1, "max": 3},
    "living_area": {"min": 1, "max": 3},
    "latitude": {"min": 1, "max": 3},
    "longitude": {"min": 1, "max": 3},
}
VALID_DATA = {
    "construction_year": 2,
    "living_area": 2,
    "latitude": 2,
    "longitude": 2,
}

INVALID_DATA = {
    "construction_year": 0,
    "living_area": 2,
    "latitude": 1,
    "longitude": 1,
}


@pytest.mark.usefixtures("mock_get_training_domain")
class TestModelInputValidator:
    @pytest.fixture(autouse=True)
    def mock_get_training_domain(self, mocker):
        mock = mocker.patch(
            "housing_pricer.valuation_api._utilities.model_input_validator._get_training_domain"
        )
        mock.return_value = TRAINING_FEATURE_DOMAIN

    def test_validate_valid_data(self):
        try:
            ModelInputValidator(**VALID_DATA)
        except ValueError:
            pytest.fail("Valid data raised a ValueError unexpectedly!")

    def test_validate_invalid_data(self):
        with pytest.raises(ValueError):
            ModelInputValidator(**INVALID_DATA)

    def test_valid_data(self):
        model_input = ModelInputValidator(**VALID_DATA)
        for attribute, value in VALID_DATA.items():
            assert (
                getattr(model_input, attribute) == value
            ), f"{attribute} does not match the expected value"
