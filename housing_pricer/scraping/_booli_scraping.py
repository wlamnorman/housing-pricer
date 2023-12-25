"""
Utilities for scraping Booli.
"""
import json

# pylint: disable=invalid-name
import logging
import re
import time
from enum import auto
from itertools import count
from pickle import PicklingError
from typing import Any

from bs4 import BeautifulSoup, Tag
from strenum import StrEnum
from tqdm import tqdm

from housing_pricer.scraping.utilities.scraper import (
    AlreadyScrapedError,
    ScrapeError,
    Scraper,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ListingType(StrEnum):
    """
    Used to differentiate between listing types.
    """

    annons = auto()
    bostad = auto()


class DataProcessingError(Exception):
    """Exception raised for errors in data processing."""

    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(self.msg)


def scrape_listings(scraper: Scraper, duration_hrs: float):
    """
    Scrapes Booli listings for a specified duration, extracting relevant data
    and saving to file.
    """

    def fetch_listings_from_search_result(
        scraper: Scraper, search_endpoint: str
    ) -> list[dict[str, Any]] | None:
        try:
            search_result = scraper.get(f"{search_endpoint}")
            return extract_listing_types_and_ids(search_result)

        except ScrapeError as exc:
            logger.info(exc)
            return None

    def process_listings(
        scraper: Scraper, listings: list[dict[str, Any]], page_nr: int, date: str
    ) -> int:
        scraped_count = 0
        for listing_meta_info in tqdm(
            listings, desc=f"Scraping from search page number {page_nr}..."
        ):
            try:
                endpoint = f"{listing_meta_info['listing_type']}/{listing_meta_info['listing_id']}"
                listing_content = scraper.get(endpoint)
                data = extract_relevant_data_as_json(listing_content)
                scraper.data_manager.append_data_to_file(
                    endpoint_id=endpoint, date=date, data=data
                )
                scraped_count += 1

            except (AlreadyScrapedError, ScrapeError, DataProcessingError) as exc:
                logger.info(exc)
            except (OSError, PicklingError) as exc:
                logger.error("%s", exc)
                continue

        return scraped_count

    start_time = time.time()
    n_listings_scraped = 0

    with scraper.data_manager:
        while time.time() - start_time < duration_hrs * 60**2:
            for date in scraper.data_manager.dates_to_scrape:
                logger.info("Starting to scrape from date: %s", date)
                for page_nr in count():
                    search_endpoint = f"sok/slutpriser?maxSoldDate={date}&minSoldDate={date}&page={page_nr}"
                    listings = fetch_listings_from_search_result(
                        scraper, search_endpoint
                    )

                    if isinstance(listings, list) and listings:
                        n_listings_scraped += process_listings(
                            scraper, listings, page_nr, date
                        )
                        logger.info(
                            "Number of listings scraped: %d", n_listings_scraped
                        )
                    else:
                        break

                logger.info("Finished scraping date: %s", date)


def extract_listing_types_and_ids(search_content: bytes) -> list[dict[str, Any]]:
    """
    Extracts listing types and IDs from the given search content.

    This function parses the provided HTML content, decoded from bytes, to find
    listings based on a URL pattern. Each listing URL includes a listing type
    ('annons' or 'bostad') and a unique numerical ID.

    Parameters
    ----------
    search_content
        The HTML content of the search page.

    Returns
    -------
        List of dictionaries, each containing a listing's type and id.
    """
    pattern = r"https://www\.booli\.se/(annons|bostad)/(\d+)"
    listings = []
    for match in re.finditer(pattern, search_content.decode()):
        listings.append(
            {"listing_type": ListingType[match.group(1)], "listing_id": match.group(2)}
        )
    return listings


def extract_market_status(parsed_html_response: BeautifulSoup) -> str:
    """Extracts market status of listings html response."""
    status = parsed_html_response.find(
        "div",
        {
            # pylint: disable=line-too-long
            "class": """py-1 rounded w-fit bg-bui-color-black text-bui-color-white inline-flex items-center justify-center font-semibold rounded px-2 text-sm"""
        },
    )
    if status:
        return status.text
    raise DataProcessingError("Entry missing market status tag.")


def extract_relevant_data_as_json(html_content: bytes | str) -> dict[str, Any]:
    """
    Process the HTML content and keep only essential data in JSON format.

    Parameters
    ----------
        html_content: The HTML content as bytes or str.

    Returns
    -------
        A dictionary containing the filtered JSON data.

    Raises:
    -------
        DataProcessingError: If any step in the data processing fails.
    """
    try:
        parsed_html = BeautifulSoup(html_content, features="lxml")
        parsed_relevant_section = parsed_html.find(
            name="script", attrs={"id": "__NEXT_DATA__"}
        )
        market_status = extract_market_status(parsed_html)

        if isinstance(parsed_relevant_section, Tag) and parsed_relevant_section.string:
            section_data_json = json.loads(s=parsed_relevant_section.string)
            relevant_data = section_data_json["props"]["pageProps"]["__APOLLO_STATE__"]
            relevant_data.pop("ROOT_QUERY", None)
            relevant_data["market_status"] = market_status
            return relevant_data

        raise DataProcessingError(
            "Relevant script tag with specified id not found in html-parser."
        )

    except json.JSONDecodeError as exc:
        raise DataProcessingError("Failed to decode JSON.") from exc
    except (KeyError, AttributeError) as exc:
        raise DataProcessingError("Error accessing data.") from exc
