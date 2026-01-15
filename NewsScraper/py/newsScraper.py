import json
import time
import os
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tflink import TFLinkClient
import ghostscript

import utils

PROJECT_ROOT = Path('/path/to/project/')

class NewsScraper:
    """
    A simple scraper for some well-known Italian newspapers
    """

    DOWNLOAD_FOLDER = PROJECT_ROOT / "downloads"
    ARCHIVE_FOLDER = PROJECT_ROOT / "archives"
    CREDENTIALS_DB = PROJECT_ROOT / "system" / "creds.creds"
    
    def __init__(self):
        """Initialize data necessary for scraping"""
        
        self.log = logging.getLogger(__name__)
        self.upload_data = ''
        self.button_text = ''
        self.date = utils.italian_date(formatter = '-')
        # Path of the archive and path where the downloaded newspaper will be download
        self.archive = ''
        self.paper_name = ''
        # Requires full knowledge of a model download link
        self.login_url = ''
        self.download_url = ''
        self.email = ''
        self.password = ''
        
        # The selenium driver
        self.driver = self._set_selenium_options()
        
        self.credentials = utils.decrypt_credentials(NewsScraper.CREDENTIALS_DB)
    
    def scrape(self):
        """Deal all the main actions of the class 
        and returns a success flag and download link/error log
        """
        if self._do_login():
            # Some time to load the page on a slow connection
            time.sleep(5)

            try:
                self._download_paper()
                # Wait for the PDF to be downloaded and get path of the downloaded file
                download_path = self._wait_for_download()
                if download_path:
                    compressed_pdf = self._compress_pdf(download_path)
                    self.upload_link = self._upload_pdf(self.paper_name, compressed_pdf)
                    # Delete all files after uploading
                    self._clear_folder()
                    if self.upload_link:
                        return True 
                    else:
                        return False
                else:
                    self.log.warning("Unable to download the pdf.")
                    return False

            except Exception as e:
                self.log.error(e)
                return False

            finally:
                self.driver.quit()
        
        else:
            return False 

    def _do_login(self):
        """Logs into the website using Selenium"""
        try:
            # Open login page
            self.driver.get(self.login_url)
            self._close_cookie_banner()

            # Explicit wait object
            wait = WebDriverWait(self.driver, 20)
            # Fill email 
            email_input = wait.until(
                EC.visibility_of_element_located((By.NAME, "lusername"))
            )
            email_input.send_keys(self.email)
            # Fill password 
            password_input = wait.until(
                EC.visibility_of_element_located((By.NAME, "lpassword"))
            )
            password_input.send_keys(self.password)
            # Click login button 
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='LOGIN']"))
            )
            login_button.click()
            time.sleep(3)

            self.log.info("Logged in.")

        except Exception as e:
             self.log.error(e)
             return False

        return True

    def _set_selenium_options(self):
        """Set the options for selenium"""
        # Chrome options
        opts = Options()
        # opts.add_argument("-headless")  # remove to debug visually

        # Use Service to specify chromedriver path
        service = Service("/usr/local/bin/chromedriver")
        prefs = {
            "download.default_directory": str(NewsScraper.DOWNLOAD_FOLDER),
            "plugins.always_open_pdf_externally": True
        }
        opts.add_experimental_option("prefs", prefs)

        self.log.info("Selenium options set.")
        
        return webdriver.Chrome(service=service, options=opts)
    
    def _close_cookie_banner(self):
        """Close the accursed cookie banner (if any)"""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{self.button_text}')]"))
            )
            cookie_button.click()
            self.log.info("Cookie banner dismissed.")
        except:
            self.log.info("No cookie banner found.")

    def _download_paper(self):
        """Minimal download method for direct download"""
        try:
            self.driver.get(self.download_url)
        except Exception as e:
            self.log.error(e)

    def _click(self, element):
        """Safe, headless click"""
        try:
            self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element
                    )

            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", element)

        except Exception as e:
            self.log.error(f"Click failed: {e}")
            raise

    def _clear_folder(self):
            """Clear the download folder"""

            for file in self.DOWNLOAD_FOLDER.iterdir():
                if file.is_file():
                    file.unlink()

    def _upload_pdf(self, paper_name, download_path):
        """ 
        Upload the attachment to tmpfile.link and returns the link 
        NOTE: TFLink occasionally blocks VPNs
        """

        path_obj = Path(download_path)
        tflink_client = TFLinkClient()
        
        try:
            # Upload the file as (e.g.) news_paper_name_04-12-45. Return the download link.
            upload_file = tflink_client.upload(
                    str(path_obj), 
                    filename=f"{paper_name}_{self.date}.pdf"
                    )
            time.sleep(10)

            self._append_to_archive(self.ARCHIVE_PATH, upload_file.download_link)
            
            # Delete the file
            self.log.info("Pdf uploaded and deleted from folder.")

            return upload_file.download_link

        except Exception as e:
            self.log.error(e)
    
    def _append_to_archive(self, archive, link):
        """Append the link to the newly-uploaded pdf link to the json archive of pdfs"""
        
        with open(archive, 'r') as f:
            complete_archive = json.load(f)

        new_edition = {f"{self.date.replace('-', ' ')}": f"{link}"}
        # Add the new edition at the beginning of the archive
        complete_archive.insert(0, new_edition)

        # Check if there are more than 7 editions and delete the oldest one
        if len(complete_archive) > 7:
            complete_archive.pop()
            self.log.info("The archive includes more than seven editions. The last one has been deleted.")

        with open(archive, 'w') as f:
            json.dump(complete_archive, f)

        self.log.info("Pdf appended to the archive.")

    def _wait_for_download(self):
        """
        Wait for download to finish by checking 
        the size of the file in the download directory
        """
        timeout = 120
        end_time = time.time() + timeout
        last_size = None
        stable_since = None
        stable_seconds = 2

        while time.time() < end_time:
            pdfs = [
                    f for f in os.listdir(NewsScraper.DOWNLOAD_FOLDER)
                    if f.lower().endswith(".pdf")
            ]
            if not pdfs:
                time.sleep(1.5)
                continue

            # Create the path to pdf
            pdf_path = os.path.join(NewsScraper.DOWNLOAD_FOLDER, pdfs[0])
            size = os.path.getsize(pdf_path)
            
            if last_size is None or size != last_size:
                stable_since = None
                last_size = size
            else:
                if stable_since is None:
                    # Initializes size if there's none yet
                    stable_since = time.time()
                elif time.time() - stable_since >= stable_seconds:
                    # If the PDF size has remained stable for at least two seconds
                    self.log.info('The PDF file is stable.')
                    return pdf_path
               
            time.sleep(1.5)
        return None

    def _compress_pdf(self, input_pdf):
        """Compress the PDF file with Ghostcript"""

        compressed_pdf = f"{input_pdf.replace('.pdf', '')}_compressed.pdf"  # Output file
        args = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/screen",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={compressed_pdf}",
            input_pdf
        ]

        ghostscript.Ghostscript(*args)
        self.log.info('The PDF file has been compressed.')
        
        return compressed_pdf 

