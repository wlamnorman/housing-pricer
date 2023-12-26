import logging
import json
from typing import Any

import pandas as pd
import xgboost as xgb

from housing_pricer.valuation_api._utilities.address_to_coordinates import (
    scrape_address_coordinates,
)
from housing_pricer.valuation_api._utilities.validation import ApartmentData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    request = read_request()
    # TODO: validate_request()
    logger.info(f"Read request {request}")

    logger.info("Scraping additional data")
    coordinates = scrape_address_coordinates(
        gata=request["address"]["street"],
        gatunummer=request["address"]["street_number"],
        ort=request["address"]["municipality"],
    )

    model_input = request | coordinates
    logger.info(f"Available data before creating model input {request}")

    dmatrix = validate_and_reformat_model_input(model_input)

    # TODO: add try-except with validation error and validate reasonable inputs (min-max of dataset for each field for starters?)
    valuator = xgb.Booster()
    valuator.load_model("xgb.json")

    valuation = valuator.predict(dmatrix)[0]
    logger.info(
        "The estimated fair value for the requested housing is %d kr.", valuation
    )


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
