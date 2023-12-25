from housing_pricer.valuation_api._utilities.validation import ApartmentData
import xgboost as xgb
import json
from typing import Any
import pandas as pd


def main():
    model_input = read_request()
    dmatrix = validate_and_reformat_model_input(model_input)

    # TODO: add try-except with validation error and validate reasonable inputs (min-max of dataset for each field for starters?)
    valuator = xgb.Booster()
    valuator.load_model("xgb.json")

    valuation = valuator.predict(dmatrix)[0]
    print(valuation)


def read_request() -> dict[str, Any]:
    with open("test_listing.json", "r") as file:
        data_dict = json.load(file)
    return data_dict


def validate_and_reformat_model_input(model_input: dict[str, Any]) -> xgb.DMatrix:
    validated_model_input = ApartmentData(**model_input)
    input_as_dmatrix = xgb.DMatrix(pd.DataFrame([validated_model_input.model_dump()]))
    return input_as_dmatrix


if __name__ == "__main__":
    main()
