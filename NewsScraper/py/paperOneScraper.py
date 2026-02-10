import logging
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from newsScraper import NewsScraper

PROJECT_ROOT = Path("/path/to/project/")


class PaperOneScraper(NewsScraper):
    """A scraper for Paper One"""

    ARCHIVE_PATH = PROJECT_ROOT / "archives" / "paper1_archive.json"

    def __init__(self, date) -> None:
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.date = date
        self.paper_name = "paper_one"
        self.button_text = "Ho capito"

        # Requires full knowledge of a model download link
        self.login_url = "https://xxxxxyyyyyzzzz.com/login"
        self.download_url = f"https://aaaaaabbbbb-{self.date}"

        self.email = self.credentials["email"]
        self.password = self.credentials["password"]

        self.log.info("Downloading il paper one...")
        self.log.info(f"Download link:\n{self.download_url}")

        self.success = self.scrape()

    def _do_login(self) -> bool:
        """Log into the newspaper website using Selenium."""
        try:
            # Open login page
            self.driver.get(self.login_url)
            self._close_cookie_banner()

            # Explicit wait object
            wait = WebDriverWait(self.driver, 20)

            # Fill email
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.send_keys(self.email)
            # Fill password
            password_input = wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.send_keys(self.password)
            # Click login button
            login_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Accedi')]")
                )
            )
            login_button.click()

            self.log.info("Logged in.")

        except Exception as e:
            self.log.error(e)
            return False

        return True

    def _compress_pdf(self, input_pdf: str) -> str:
        """No need to compress this paper"""
        return input_pdf
