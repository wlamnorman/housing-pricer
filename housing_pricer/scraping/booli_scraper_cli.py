"""
This module provides a command-line interface for scraping housing listings 
from the Booli website.
"""

import click

from housing_pricer.scraping._booli_scraping import scrape_listings
from housing_pricer.scraping.sdk.data_manager import DataManager
from housing_pricer.scraping.sdk.scraped_dates_manager import ScrapedDatesManager
from housing_pricer.scraping.sdk.scraper import Scraper

DATA_STORAGE_PATH: str = "data_storage"


@click.command()
@click.option(
    "--scraping_duration_hrs",
    "-d",
    required=True,
    help="Duration of scraping in hours.",
    type=float,
)
@click.option(
    "--max_requests_per_minute",
    "-r",
    help="""Max number of requests to website per minute.
            >200 does not give any speed increase.
            NOTE: higher values mean higher risk of being flagged.""",
    default=200,
    type=int,
)
def main(scraping_duration_hrs: float, max_requests_per_minute: int):
    """
    initializes the scraper and DataManager, and starts the scraping process.
    """

    def _input_validation():
        assert scraping_duration_hrs > 0

    _input_validation()

    booli_scraper = Scraper(
        base_url="https://www.booli.se/",
        data_manager=DataManager(DATA_STORAGE_PATH),
        max_requests_per_minute=max_requests_per_minute,
        max_delay_seconds=20,
    )
    scraped_dates_manager = ScrapedDatesManager(DATA_STORAGE_PATH)
    scrape_listings(
        scraper=booli_scraper,
        scraped_dates_manager=scraped_dates_manager,
        duration_hrs=scraping_duration_hrs,
    )


if __name__ == "__main__":
    main()
