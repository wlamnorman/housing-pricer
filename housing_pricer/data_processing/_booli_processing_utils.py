"""
Data processing utilities for Booli listings.
"""

import json
from typing import Any

from bs4 import BeautifulSoup

KEY_MAPPING = {
    "streetAddress": "address",
    "soldPrice": "sold_price",
    "listPrice": "list_price",
    "livingArea": "living_area",
    "montlyPayment": "monthly_payment",
    "constructionYear": "construction_year",
    "addressLocality": "locality",
    "addressRegion": "region",
    "addressCountry": "country",
    "postalCode": "postal_code",
}


def extract_ad_info(listing: str) -> dict[str, Any]:
    listing_soup = BeautifulSoup(listing, features="lxml")
    listing_details = {}

    if price_details := extract_price_details(listing_soup):
        listing_details |= price_details

    # if address_details := extract_address_details(listing_soup):
    #     listing_details |= address_details

    return {KEY_MAPPING[k]: listing_details[k] for k in listing_details if k in KEY_MAPPING}


def extract_price_details(soup: BeautifulSoup) -> dict[str, int] | None:
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if script_tag:
        try:
            data = json.loads(script_tag.string)  # type: ignore
            property_details = {}

            for key, value in (
                data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {}).items()
            ):
                if key.startswith("SoldProperty:"):
                    property_details["soldPrice"] = value.get("soldPrice", {}).get("raw")
                    property_details["listPrice"] = value.get("listPrice", {}).get("raw")

                    property_details["livingArea"] = value.get("livingArea", {}).get("raw")
                    property_details["rooms"] = value.get("rooms", {}).get("raw")
                    property_details["monthlyPayment"] = value.get("rent", {}).get("raw")
                    property_details["constructionYear"] = value.get("constructionYear")

                    property_details["latitude"] = value.get("latitude")
                    property_details["longitude"] = value.get("longitude")

                    return property_details

        except json.JSONDecodeError as exc:
            raise RuntimeError() from exc
        except KeyError as exc:
            raise RuntimeError() from exc


# def extract_address_details(soup: BeautifulSoup) -> dict[str, Any] | None:
#     script_tags = soup.find_all("script", {"type": "application/ld+json"})
#     for tag in script_tags:
#         try:
#             data = json.loads(tag.string)
#             if data["@type"] == "Place" and "address" in data:
#                 if isinstance(address_data := data["address"], dict):
#                     address_data.pop("@type", None)
#                     return address_data
#                 else:
#                     raise ValueError(f"Address data is of unexpected type: {type(address_data)}")

#         except json.JSONDecodeError as exc:
#             raise RuntimeError() from exc
#         except KeyError as exc:
#             raise RuntimeError() from exc
