"""
Utilities for scraping Booli.
"""
import json

# pylint: disable=invalid-name
import logging
import re
import time
from enum import auto
from pickle import PicklingError
from typing import Any, Iterable

from bs4 import BeautifulSoup, Tag
from strenum import StrEnum
from tqdm import tqdm

from housing_pricer.scraping.scraper import AlreadyScrapedError, ScrapeError, Scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEARCH: str = "sok/slutpriser?areaIds=2&objectType=Lägenhet&sort=soldDate"


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


def scrape_listings(scraper: Scraper, page_nr: int, duration_hrs: float):
    """
    Scrapes Booli listings for a specified duration, extracting relevant data 
    and saving to file.
    """

    def fetch_listings_from_search_result(
        scraper: Scraper, page_nr: int
    ) -> Iterable[dict[str, Any]] | None:
        try:
            search_result = scraper.get(
                f"{SEARCH}&page={page_nr}",
                mark_endpoint=False,
            )
            return extract_listing_types_and_ids(search_result)
        except ScrapeError as exc:
            logger.info(exc)
            return None

    def process_listings(scraper: Scraper, listings: Iterable[dict[str, Any]]) -> int:
        scraped_count = 0
        for listing_meta_info in tqdm(
            listings, desc=f"Scraping from search page number {page_nr}..."
        ):
            try:
                listing_content = scraper.get(
                    f"{listing_meta_info['listing_type']}/{listing_meta_info['listing_id']}",
                    mark_endpoint=True,
                )
                data = extract_relevant_data_as_json(listing_content)
                scraper.data_manager.append_data_to_file(data)
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
            listings = fetch_listings_from_search_result(scraper, page_nr)
            if listings is not None:
                n_listings_scraped += process_listings(scraper, listings)

                logger.info("Number of listings scraped: %d", n_listings_scraped)
                page_nr += 1


def extract_listing_types_and_ids(search_content: bytes) -> Iterable[dict[str, Any]]:
    """
    Extracts listing types and IDs from the given search content.

    This function parses the provided HTML content, decoded from bytes, to find
    listings based on a URL pattern. Each listing URL includes a listing type
    ('annons' or 'bostad') and a unique numerical ID.

    Parameters
    ----------
    search_content
        The HTML content of the search page.

    Yields
    ------
        A dictionary for each listing, containing its listing type and listing id.
    """
    pattern = r"https://www\.booli\.se/(annons|bostad)/(\d+)"
    for match in re.finditer(pattern, search_content.decode()):
        yield {"listing_type": ListingType[match.group(1)], "listing_id": match.group(2)}


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
        parsed_relevant_section = parsed_html.find(name="script", attrs={"id": "__NEXT_DATA__"})

        if isinstance(parsed_relevant_section, Tag) and parsed_relevant_section.string:
            data_json = json.loads(s=parsed_relevant_section.string)
            filtered_data_json = {
                key: data_json[key] for key in ["props", "page", "query"] if key in data_json
            }
            return filtered_data_json
        raise DataProcessingError("Relevant script tag with specified id not found in html-parser.")

    except json.JSONDecodeError as exc:
        raise DataProcessingError("Failed to decode JSON.") from exc
    except (KeyError, AttributeError) as exc:
        raise DataProcessingError("Error accessing data.") from exc
    except Exception as exc:
        raise DataProcessingError("Error") from exc
