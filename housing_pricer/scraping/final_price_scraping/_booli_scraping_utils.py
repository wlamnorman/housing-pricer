from typing import Iterable, Any
import re
import json
from bs4 import BeautifulSoup
from enum import auto
from strenum import StrEnum
from tqdm import tqdm

from housing_pricer.scraping.base_scraper import Scraper
from housing_pricer.scraping.data_manager import DataManager


KEY_MAPPING = {
    "soldPrice": "sold_price",
    "listPrice": "list_price",
    "livingArea": "living_area",
    "montlyPayment": "monthly_payment",
    "constructionYear": "construction_year",
    "streetAddress": "address",
    "addressLocality": "locality",
    "addressRegion": "region",
    "addressCountry": "country",
    "postalCode": "postal_code",
}


class ListingType(StrEnum):
    annons = auto()
    bostad = auto()


def scrape_and_store_search_page(search_result: bytes, scraper: Scraper, data_manager: DataManager):
    for listing in tqdm(
        extract_listings(search_result), desc="Collecting search page's listing details"
    ):
        listing_type = listing[0]
        listing_id = listing[1]
        assert listing_type in [ListingType.annons, ListingType.bostad]

        try:
            listing = scraper.get(f"{listing_type}/{listing_id}").decode()
            listing_info = extract_ad_info(listing, listing_id)

        except Exception as exc:
            print(exc)
            continue

        data_manager.append_data_to_file(file_name="testing", data=listing_info)


def extract_listings(content: bytes) -> Iterable[tuple[str, Any]]:
    """Extracts bostad/annons : listing ids key-value pairs from a booli
    search response of the form `https://www.booli.se/sok/slutpriser?...`."""
    content_ = content.decode()

    annons_pattern = r"https://www\.booli\.se/annons/(\d+)"
    for match in re.finditer(annons_pattern, content_):
        yield (ListingType.annons, match.group(1))

    bostad_pattern = r"https://www\.booli\.se/bostad/(\d+)"
    for match in re.finditer(bostad_pattern, content_):
        yield (ListingType.bostad, match.group(1))


def extract_address_details(soup: BeautifulSoup) -> dict[str, Any] | None:
    script_tags = soup.find_all("script", {"type": "application/ld+json"})
    for tag in script_tags:
        try:
            data = json.loads(tag.string)
            if data["@type"] == "Place" and "address" in data:
                if isinstance(address_data := data["address"], dict):
                    address_data.pop("@type", None)
                    return address_data
                else:
                    raise ValueError(f"Address data is of unexpected type: {type(address_data)}")

        except json.JSONDecodeError as exc:
            raise RuntimeError() from exc
        except KeyError as exc:
            raise RuntimeError() from exc


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


def extract_ad_info(listing: str, listing_id: str) -> dict[str, Any]:
    listing_soup = BeautifulSoup(listing, features="html.parser")
    listing_details = {"id": listing_id}

    if price_details := extract_price_details(listing_soup):
        listing_details |= price_details

    if address_details := extract_address_details(listing_soup):
        listing_details |= address_details

    return {KEY_MAPPING[k]: listing_details[k] for k in listing_details if k in KEY_MAPPING}
