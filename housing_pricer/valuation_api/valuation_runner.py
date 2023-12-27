import logging
import json
from typing import Any

import pandas as pd
import xgboost as xgb

from housing_pricer.valuation_api._utilities.geocode_address import (
    geocode_address,
)
from housing_pricer.valuation_api._utilities.model_input_validator import (
    ModelInputValidator,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    request = read_request()
    logger.info(f"Read request {request}, attemping valuation...")

    coordinates = geocode_address(
        gata=request["address"]["street"],
        gatunummer=request["address"]["street_number"],
        ort=request["address"]["municipality"],
    )

    model_input = request | coordinates
    validated_model_input = ModelInputValidator(**model_input)
    dmatrix = xgb.DMatrix(pd.DataFrame([validated_model_input.model_dump()]))

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


if __name__ == "__main__":
    main()
