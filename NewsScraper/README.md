# NewsScraper

A simple yet powerful news scraper

## Overview

A scraper that logs into the website of a well-known Italian newspaper, downloads the daily edition in PDF format, uploads it to an upload service, and finally emails it to a list of recipients through my personal gmail. The email will also include a list of the last six editions. 
The credentials (gmail token, newspaper website password and emails) are securely stored in a Fernet-encrypted file. The Fernet key is stored in a separate file. The address book is in json format, and so is the archive of editions.
For robustness, the program preserves a timestamped log. Should anything fail, the log is sent to the sender of the email (my personal email).  
NOTE: A subscription is needed to download the newspaper.

## Goals of the project: 
1. Sinking my teeth into more structured and advanced Python.
2. The sheer intellectual challenge of it.
3. The fun that comes with automating otherwise tedious tasks.
4. Having my Raspberry Pi send me the newspaper every morning.

## Key features
- Fast and safe encryption of all sensitive data via Fernet
- An archive of editions update daily
- Very easily extendable
- A command line interface which allows for debugging purposes, test runs, and easy manipulation of the address book.  
(You can the program run with the "-i" flag to access the command line interface, or the "-y" flag to test with yesterday's edition)

## Technologies
- Python3, pure and simple
- Core libraries: Selenium, Fernet, TFLink
- Standard libraries: os, datetime, smtplib, argparse, pathlib, locale

## Structure
- main.py
- NewsScraper.py --> the class that does the scraping
- Mailer class --> the class that emails the result
- utils.py --> tangential but usual functions that did not fit any of the classes above

## Setup
- I have set it up with this crontab on my Raspberry Pi:
  
30 23 * * 2-7 /path/to/venv/bin/python3 /path/to/script/main.py >> /path/to/log/cronlog.log 2>&1  
  
(There's no newspaper on Mondays)  
NOTE: If you decided to install the crontab make sure to use absolute paths in the script!


Tested on Debian 13 (Trixie) and Raspberry Pi OS
