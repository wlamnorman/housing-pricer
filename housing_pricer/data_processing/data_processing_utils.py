"""
Data processing utilities for Booli listings.
"""
from typing import Any, Iterable

import pandas as pd
from tqdm import tqdm

JSONDataType = dict[str, Any]


class MissingDataError(Exception):
    """
    Error to throw if data is missing.
    """


def format_json_to_dataframe(data: Iterable[JSONDataType]) -> pd.DataFrame:
    """
    Processes scraped JSON data, extracts details and reformats to dataframe.
    """

    def get_sold_property_details(entry: JSONDataType) -> dict[str, Any]:
        for data_keys, property_details in entry["data"].items():
            if data_keys.startswith(("SoldProperty:", "Listing:")):
                return property_details

        entry_id: str = entry["id"]
        raise MissingDataError(
            f"Entry with ID: {entry_id} has no 'SoldProperty' or 'Listing' data key."
        )

    def parse_url_id(entry: JSONDataType):
        """
        Example
        -------
        'bostad/2556516' -> {'listing_type': 'bostad', 'listing_id': 2556516}
        """
        parts = entry["id"].split("/")
        return {"url_listing_type": parts[0], "url_listing_id": int(parts[1])}

    def get_previous_sales(property_details: JSONDataType) -> JSONDataType:
        previous_sales: list[int] = []
        if (
            isinstance(property_details, dict)
            and "salesOfResidence" in property_details
            and property_details["salesOfResidence"] is not None
        ):
            for sale in property_details["salesOfResidence"]:
                previous_sales.append(int(sale["booliId"]))
        return {
            "booli_ids_of_previous_sales": previous_sales,
            "n_previous_sales": len(previous_sales),
        }

    listings = []
    for entry in tqdm(data, desc="Processing scraped JSON content to dataframe..."):
        try:
            property_details = get_sold_property_details(entry)
        except MissingDataError:
            continue

        extracted_details = (
            parse_url_id(entry)
            | {
                "booli_id": property_details.get("booliId"),
                "sold_date": property_details.get("soldDate"),
                "days_listed": property_details.get("daysActive"),
                "residence_type": property_details.get("objectType"),
                "address": property_details.get("streetAddress"),
                "apartment_number": get_nested_dict_value(
                    property_details, ["apartmentNumber", "value"]
                ),
                "urban_area": property_details.get("descriptiveAreaName"),
                "municipality": get_nested_dict_value(
                    property_details, ["location", "region", "municipalityName"]
                ),
                "construction_year": property_details.get("constructionYear"),
                "list_price": get_nested_dict_value(property_details, ["listPrice", "raw"]),
                "sold_price": get_nested_dict_value(property_details, ["soldPrice", "raw"]),
                "sold_price_type": property_details.get("soldPriceType"),
                "first_price": get_nested_dict_value(property_details, ["firstPrice", "value"]),
                "monthly_payment": get_nested_dict_value(
                    property_details, ["monthlyPayment", "formatted"]
                ),
                "rent": get_nested_dict_value(property_details, ["rent", "raw"]),
                "operating_cost": get_nested_dict_value(property_details, ["operatingCost", "raw"]),
                "energy_class": get_nested_dict_value(property_details, ["energyClass", "score"]),
                "floor": get_nested_dict_value(property_details, ["floor", "value"]),
                "building_floors": property_details.get("buildingFloors"),
                "latitude": property_details.get("latitude"),
                "longitude": property_details.get("longitude"),
                "has_solar_panels": property_details.get("hasSolarPanels"),
                "agency_id": property_details.get("agencyId"),
                "agent_id": property_details.get("agentId"),
            }
            | get_previous_sales(property_details)
        )
        listings.append(extracted_details)
    return pd.DataFrame(listings)


def get_nested_dict_value(dictionary: dict, keys: Iterable) -> Any:
    """
    Retrieves a nested value from a dictionary based on a list of keys.

    Parameters
    ----------
    dictionary
        The dictionary to search through.
    keys
        A list of keys representing the path to the desired value. Note
        that the keys have the been given in order of access.

    Returns:
        The value found at the nested location, or None if any key is missing
        or invalid.
    """
    current_value = dictionary
    for key in keys:
        if isinstance(current_value, dict) and key in current_value:
            current_value = current_value[key]
        else:
            return None

    return current_value
