import json
import time
import os
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tflink import TFLinkClient

from utils import decrypt_credentials

class NewsScraper:
    """A simple scraper for a well-known Italian newspaper"""

    def __init__(self, date):
        """Initialize data necessary for scraping"""
        self.date = date
        self.upload_data = ''
        self.log = f"***{datetime.now()}***\n"
        
        # Path of the archive and path where the downloaded newspaper will be download
        self.archive = 'archive.json'
        self.paper_path = "/path/to/project/folder/"
        # Requires full knowledge of a model download link
        self.login_url = "https://login-url"
        self.download_url = f"https://name-of-newspaper-{self.date}"
        self.log += f"Download link:\n{self.download_url}\n"
        
        # The selenium driver
        self.driver = self._set_selenium_options()
        
        credentials = decrypt_credentials("creds.creds")
        self.email = credentials['email']
        self.password = credentials['password']
        self.success, self.result = self.scrape()

    def scrape(self):
        """Deal all the main actions of the class 
        and returns a success flag and download link/error log
        """
        if self._do_login():
            # Some time to load the page on a slow connection
            time.sleep(5)

            try:
                self.driver.get(self.download_url)
                time.sleep(10)
                # Wait for the PDF to be downloaded
                if self._wait_for_download():
                    self.upload_data = self._upload_pdf()
                    if self.upload_data:
                        return True, self.upload_data
                    else:
                        return False, self.log
                else:
                    self.log += "\nUnable to download the pdf."
                    return False, self.log

            except Exception as e:
                self.log += f"\n{e}"
                return False, self.log

            finally:
                self.driver.quit()
        
        else:
            return False, self.log

    def _do_login(self):
        """Log into the newspaper website using Selenium."""
        try:
            # Open login page
            self.driver.get(self.login_url)
            self._close_cookie_banner()

            # Explicit wait object
            wait = WebDriverWait(self.driver, 20)

            # Fill email 
            email_input = wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.send_keys(self.email)
            # Fill password 
            password_input = wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.send_keys(self.password)
            # Click login button 
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accedi')]"))
            )
            login_button.click()
            
            self.log += '\nLogged in.'
        
        except Exception as e:
             self.log += f"\n{e}"
             return False

        return True

    def _set_selenium_options(self):
        """Set the options for selenium"""
        # Chrome options
        opts = Options()
        opts.add_argument("-headless")  # remove to debug visually

        # Use Service to specify chromedriver path
        service = Service("path/to/chromedriver")
        prefs = {
            "download.default_directory": "/path/to/download/directory",
            "plugins.always_open_pdf_externally": True
        }
        opts.add_experimental_option("prefs", prefs)

        self.log += "Selenium options set."
        
        return webdriver.Chrome(service=service, options=opts)
    
    def _close_cookie_banner(self):
        """Close the accursed cookie banner (if any)"""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Ho capito')]"))
            )
            cookie_button.click()
            self.log += "\nCookie banner dismissed."
        except:
            self.log += "\nNo cookie banner found."
    
    def _upload_pdf(self):
        """ 
        Upload the attachment to tmpfile.link and returns the link 
        NOTE: TFLink occasionally blocks VPNs
        """

        path_obj = Path(f"{self.paper_path}il-[newspaper name]-del-{self.date}.pdf")
        tflink_client = TFLinkClient()
        
        try:
            # Upload the file as (e.g.) news_paper_name_04-12-45. Return the download link.
            upload_file = tflink_client.upload(path_obj, filename=f"il-[newspaper name]-del-{self.date}.pdf")
            time.sleep(10)

            self._append_to_archive(upload_file.download_link)
            
            # Delete the file
            path_obj.unlink()
            self.log += "\nPdf uploaded and deleted from folder."

            return upload_file.download_link

        except Exception as e:
            self.log += f"\n{e}"
            return False
    
    def _append_to_archive(self, link):
        """Append the link to the newly-uploaded pdf link to the json archive of pdfs"""
        
        with open(self.archive, 'r') as f:
            complete_archive = json.load(f)

        new_edition = {f"{self.date.replace('-', ' ')}": f"{link}"}
        # Add the new edition at the beginning of the archive
        complete_archive.insert(0, new_edition)

        # Check if there are more than 7 editions and delete the oldest one
        if len(complete_archive) > 7:
            complete_archive.pop()
            self.log += "\nThe archive includes more than seven editions. The last one has been deleted."

        with open(self.archive, 'w') as f:
            json.dump(complete_archive, f)

        self.log += "\nPdf appended to the archive."

    def _wait_for_download(self):
        """Waits for the download to pop up in the download folder"""
        timeout = 30
        end_time = time.time() + timeout
        while time.time() < end_time:
            files = os.listdir('.')
            if any(f.endswith(".pdf") for f in files):
                return True
            time.sleep(1)
        return False

