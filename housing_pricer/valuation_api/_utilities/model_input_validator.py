import json
from pydantic import BaseModel, field_validator, ValidationInfo


def _get_training_domain():
    with open("_utilities/training_domain.json") as file:
        training_domain = json.load(file)
    return training_domain


class ModelInputValidator(BaseModel):
    construction_year: int
    living_area: float
    latitude: float
    longitude: float

    @field_validator("construction_year", "living_area", "latitude", "longitude")
    @classmethod
    def check_all_fields(cls, value, info: ValidationInfo):
        training_domain = _get_training_domain()
        if info.field_name in training_domain:
            min_val = training_domain[info.field_name]["min"]
            max_val = training_domain[info.field_name]["max"]
            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"{info.field_name} must be between {min_val} and {max_val}"
                )
        return value
