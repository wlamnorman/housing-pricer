"""
Utilities for scraping Booli.
"""
# pylint: disable=invalid-name
import re
from enum import auto
from typing import Any, Iterable

from strenum import StrEnum


class ListingType(StrEnum):
    """
    Used to differentiate between listing types.
    """

    annons = auto()
    bostad = auto()


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
