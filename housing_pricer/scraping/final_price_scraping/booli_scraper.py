from housing_pricer.scraping.base_scraper import Scraper
from housing_pricer.scraping.data_manager import DataManager
from _booli_scraping_utils import scrape_and_store_search_page

DATA_STORAGE_PATH: str = "data_storage"


def main():
    booli_scraper = Scraper(base_url="https://www.booli.se/")
    data_manager = DataManager(DATA_STORAGE_PATH)

    search_result = booli_scraper.get("sok/slutpriser?areaIds=2&objectType=Lägenhet")
    scrape_and_store_search_page(search_result, booli_scraper, data_manager)


if __name__ == "__main__":
    main()
