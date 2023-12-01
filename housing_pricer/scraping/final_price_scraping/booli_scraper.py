from housing_pricer.scraping.scraper import Scraper
from housing_pricer.scraping.data_manager import DataManager
from _booli_scraping_utils import scrape_and_store_search_page

DATA_STORAGE_PATH: str = "data_storage"
DATA_STORAGE_FILE_NAME: str = "listings_test"

def main():
    data_manager = DataManager(DATA_STORAGE_PATH)
    booli_scraper = Scraper("https://www.booli.se/", data_manager)

    search_result = booli_scraper.get(
        "sok/slutpriser?areaIds=2&objectType=Lägenhet", mark_endpoint=False
    )
    scrape_and_store_search_page(search_result, booli_scraper, data_manager, DATA_STORAGE_FILE_NAME)


if __name__ == "__main__":
    main()
