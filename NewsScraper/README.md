# NewsScraper

A simple yet powerful news scraper

## Overview

A scraper that logs into the website of some well-known Italian newspapers, downloads the daily editions in PDF format, uploads them to an upload service, and emails them to a list of recipients through a configured SMTP service.  
All credentials are securely Fernet-encrypted and stored in a .creds file; the encryption key is stored separately. 
For robustness, the program preserves a timestamped log.   
NOTE: A subscription is needed to download the newspapers.

## Goals of the project: 
1. Sinking my teeth into more structured and advanced Python.
2. Automating otherwise tedious tasks.
3. Having my Raspberry Pi send me the newspaper every morning. It saves me 20 minutes a day!

## Key features
- Fast and safe encryption
- Up to ~60% PDF compression
- Robust exception handling
- An archive of editions updated daily
- Very easily extendable
- A command line interface which provides test runs and easy manipulation of the address book.  
(You can run the program with the "-i" flag to access the command line interface, or the "-y" flag to test with yesterday's edition)

## Technologies
- Python3, pure and simple
- Core libraries: Selenium, Fernet, TFLink, Ghostscript
- Standard libraries: os, time, datetime, smtplib, argparse, pathlib, locale, logging

## Structure
- main.py
- NewsScraper.py --> the parent scraper class
- paperOneScraper,paperTwoScraper, paperThreeScraper --> children classes (each website has different login and download methods)
- Mailer class --> the class that emails the editions
- utils.py --> generic-use functions shared between functions

## Setup
I have installed it on crontab on my Raspberry Pi:
  
0 5 * * * /path/to/venv/bin/python3 /path/to/script/main.py >> /path/to/log/cronlog.log 2>&1  
  
NOTE: If you decide to install the crontab make sure to use absolute paths in the script!      
  
  
Tested on Debian 13 (Trixie) and Raspberry Pi OS
