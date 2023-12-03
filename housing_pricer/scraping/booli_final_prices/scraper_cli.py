"""
This module provides a command-line interface for scraping housing listings 
from the Booli website.
"""

import click

from housing_pricer.scraping.booli_final_prices._scraping import scrape_listings
from housing_pricer.scraping.data_manager import DataManager
from housing_pricer.scraping.scraper import Scraper

DATA_STORAGE_PATH: str = "test"
DATA_STORAGE_FILE_NAME: str = "listings_raw_html_content"


@click.command()
@click.option(
    "--scraping_duration_hrs",
    "-d",
    required=True,
    help="Duration of scraping in hours.",
    type=float,
)
@click.option(
    "--start_page",
    "-p",
    help="Page number to start scraping from.",
    default=0,
    type=int,
)
def main(scraping_duration_hrs: float, start_page: int):
    """
    initializes the scraper and DataManager, and starts the scraping process.
    """

    def _input_validation():
        assert scraping_duration_hrs > 0
        assert start_page >= 0 and isinstance(start_page, int)

    _input_validation()

    booli_scraper = Scraper(
        base_url="https://www.booli.se/",
        data_manager=DataManager(DATA_STORAGE_PATH),
        max_requests_per_minute=150,  # no speed increase beyond 150ish
        max_delay_seconds=20,
    )
    scrape_listings(
        scraper=booli_scraper,
        data_storage_file_name=DATA_STORAGE_FILE_NAME,
        page_nr=start_page,
        duration_hrs=scraping_duration_hrs,
    )


if __name__ == "__main__":
    main()
