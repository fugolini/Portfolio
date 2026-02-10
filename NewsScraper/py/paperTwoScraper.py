import logging
import time
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from newsScraper import NewsScraper

PROJECT_ROOT = Path("/path/to/project/")


class PaperTwoScraper(NewsScraper):
    """A scraper for Paper Two"""

    ARCHIVE_PATH = PROJECT_ROOT / "archives" / "paper2_archive.json"

    def __init__(self) -> None:
        """Initialize paper-specific variables and run the scraper"""
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.email = self.credentials["email"]
        self.password = self.credentials["password"]

        self.login_url = "https://xxxxxxxxyyyyyyyyy.com/login"
        self.download_url = "https://xxxxxxxyyyyy.com/download"
        self.button_text = "Accetta"
        self.paper_name = "paper_two"

        self.log.info("Downloading Paper Two...")
        self.log.info(f"Download link:\n{self.download_url}")

        self.success = self.scrape()

    def _download_paper(self) -> None:
        """Download the paper"""
        try:
            self.driver.get(self.download_url)
            self._close_cookie_banner()

            download_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Scarica pdf')]")
                )
            )
            self._click(download_button)
            time.sleep(10)

        except Exception as e:
            self.log.error(e)
