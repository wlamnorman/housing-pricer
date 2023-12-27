"""
Defines the a Google maps scraper that can take an address and return its coordinates.
"""

import asyncio
import re

from pyppeteer import launch


def geocode_address(gata: str, gatunummer: str, ort: str):
    """
    Asyncio wrapper for scraping coordinates from address using Google Maps.
    """
    coordinates = asyncio.run(
        _scrape_google_maps_address_coordinates(gata, gatunummer, ort)
    )
    return coordinates


async def _scrape_google_maps_address_coordinates(gata: str, gatunummer: str, ort: str):
    """
    1. Opens a headless browser and goes to url corresponding to a address search.
    2. Constents to cookies.
    3. Waits to be re-directed to a page with coordinates in URL.
    4. Extracts coordinates from URL.
    """
    base_url = "https://www.google.com/maps/place/"
    url = base_url + _format_search_query(gata, gatunummer, ort)

    browser = await launch(headless=True)
    page = await browser.newPage()

    await page.goto(url)

    # wait for search button to appear on page
    await page.waitForSelector(".basebutton.button.searchButton")

    # evaluate JavaScript to click the consent button
    await page.evaluate(
        """() => {
        let buttons = document.querySelectorAll('.basebutton.button.searchButton');
        buttons.forEach(button => {
            if (button.getAttribute('aria-label') === 'Godkänn alla') {
                button.click();
            }
        });
    }"""
    )

    # wait until fully re-directed to url with coordinates
    await page.waitForNavigation({"waitUntil": "networkidle0"})

    # nasty way to ensure that url has updated
    for _ in range(100):
        try:
            coordinates = _extract_coordinates(page.url)
            await browser.close()
            return coordinates
        except RuntimeError:
            await asyncio.sleep(0.1)

    await browser.close()
    raise RuntimeError(
        f"""Address coordinates could not be scraped: given url {url}, url at exit {page.url}
                       """
    )


def _extract_coordinates(url: str) -> dict[str, float]:
    """
    Example:
    --------
    >>> url = '.../maps/place/.../@59.4430162,18.0678478,...'
    >>> extract_coordinates(url)
    {'latitude': 59.4430162, 'longitude': 18.0678478}
    """
    coordinate_pattern = r"@(.*?),(.*?),"
    match_ = re.search(coordinate_pattern, url)
    if match_ is None:
        raise RuntimeError(f"Could not derive coordinates from {url}")

    coordinates = {
        "latitude": float(match_.group(1)),
        "longitude": float(match_.group(2)),
    }
    return coordinates


def _format_search_query(gata: str, gatunummer: str, ort: str) -> str:
    """
    Example:
    --------
    >>> format_endpoint(gata="Attundavägen", gatunummer=14, ort="Täby")
    'Attundavägen+14,+Täby'
    """
    formatted_search_query = f"{gata}+{gatunummer},+{ort}"
    return formatted_search_query
