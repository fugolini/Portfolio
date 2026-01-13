import argparse
import logging

from pathlib import Path

import utils
from mailer import Mailer
from paperOneScraper import PaperOneScraperScraper
from paperTwoScraper import PaperTwoScraperScraper
from paperThreeScraper import PaperThreeScrapereScraper


PROJECT_ROOT = Path('/path/to/project/')
LOG_FOLDER = PROJECT_ROOT / "logs"


def main():
    """Enter interactive mode or run the script in standard mode"""
    
    initialize_log()

    logo = """
                _   __                  _____                                
               / | / /__ _      _______/ ___/______________ _____  ___  _____
              /  |/ / _ * | /| / / ___/*__ */ ___/ ___/ __ `/ __ */ _ */ ___/
             / /|  /  __/ |/ |/ (__  )___/ / /__/ /  / /_/ / /_/ /  __/ /    
            /_/ |_/*___/|__/|__/____//____/*___/_/   *__,_/ .___/*___/_/     
                                                         /_/                 
    """
    options = """
    Options:

    t: test run
    p: print mailing list
    a: add recipient to mailing list
    r: remove recipient from mailing list
    q: exit
    """
    parser = argparse.ArgumentParser(description=options)
    # Note that argparse automatically creates variable based on '--flag'
    parser.add_argument(
            "-i", "--interactive",
            action="store_true",
            help="Run in interactive mode"
            )
    parser.add_argument(
            "-y", "--yesterday",
            action="store_true",
            help="Scrape yesterday's newspaper"
            )
    args = parser.parse_args()
    
    if args.interactive: # Interactive mode
        print(logo)
        while True:
            choice = print("Welcome to the NewsScraper command line interface.")
            print(options)
            choice = input("What would you like to do? ")
            if choice == 'q':
                print('Exiting')
                break
            elif choice == 't':
                day = input("\tWhat day for a test run? (-1 = yesterday, -2 = two days ago...) ")
                run_scraper(int(day)) 
            elif choice == 'p':
                utils.print_address_book()
            elif choice == 'a':
                to_add = input("Recipient to add: ")
                utils.add_recipient(to_add)
            elif choice == 'r':
                to_remove = input('Recipient to remove: ')
                utils.remove_recipient(to_remove)
    elif args.yesterday == '-y': # Argument to make to run the scraper for yesterday's paper
        run_scraper(-1)
    else: 
       run_scraper()


def initialize_log():
    """Initialize the log shared across modules"""
   
    logging.basicConfig(
            filename= LOG_FOLDER / f"{utils.italian_date(formatter='_')}.log",
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )


def run_scraper(day=-1):
    """Run the main functionalities of the scraper"""
    
    mani_day = utils.italian_date(which_day=day, formatter='-')

    paper_one = PaperOneScraper(mani_day)
    paper_two = PaperTwoScraper()
    paper_three = PaperThreeScraper()

    if paper_one.success or paper_two.success or paper_three.success:
        Mailer()
    else:
        Mailer(error=True)


if __name__ == "__main__":
    main()

