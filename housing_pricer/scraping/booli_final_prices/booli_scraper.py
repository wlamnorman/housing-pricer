import logging
import time
from pickle import PicklingError

from tqdm import tqdm

from housing_pricer.scraping.booli_modelling_data._booli_scraping_utils import (
    extract_listing_types_and_ids,
)
from housing_pricer.scraping.data_manager import DataManager
from housing_pricer.scraping.scraper import AlreadyScrapedError, ScrapeError, Scraper

DATA_STORAGE_PATH: str = "data_storage"
DATA_STORAGE_FILE_NAME: str = "listings_raw_html_content"

SCRAPING_DURATION_HRS: int = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    data_manager = DataManager(DATA_STORAGE_PATH)
    booli_scraper = Scraper("https://www.booli.se/", data_manager)

    scraping_duration_sec = SCRAPING_DURATION_HRS * 60**2
    start_time = time.time()
    page_nr = 0
    n_listings_scraped = 0

    while time.time() - start_time < scraping_duration_sec:
        search_result = booli_scraper.get(
            f"sok/slutpriser?areaIds=2&objectType=Lägenhet&sort=soldDate&page={page_nr}",
            mark_endpoint=False,
        )

        for listing_meta_info in tqdm(
            extract_listing_types_and_ids(search_result),
            desc=f"Scraping from search page number {page_nr}...",
        ):
            listing_type = listing_meta_info["listing_type"]
            listing_id = listing_meta_info["listing_id"]
            # scrape listing
            try:
                listing_content = booli_scraper.get(
                    f"{listing_type}/{listing_id}", mark_endpoint=True
                ).decode()
                if not listing_content:
                    logger.info(
                        "Empty content for listing %s, skipping.", f"{listing_type}/{listing_id}"
                    )
                    continue

            except (AlreadyScrapedError, ScrapeError) as exc:
                logger.info(exc)
                continue

            # save to file
            try:
                data_manager.append_data_to_file(
                    file_name=DATA_STORAGE_FILE_NAME, data=listing_content
                )
                n_listings_scraped += 1
            except (OSError, PicklingError) as exc:
                logger.error("%s", exc)
                continue

        logger.info("Scraped %d listings from %d pages", n_listings_scraped, page_nr)
        page_nr += 1


if __name__ == "__main__":
    main()
