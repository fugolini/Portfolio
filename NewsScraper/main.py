import argparse

from mailer import Mailer
from newsScraper import NewsScraper
import utils

def main():
    """Enter interactive mode or run the script in standard mode"""
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

def run_scraper(day=0):
    """Run the main functionalities of the scraper"""
    today = utils.italian_date(which_day=day, formatter='-')
    scraping = NewsScraper(today)
    if scraping.success == True:
        Mailer(log=scraping.log)
    else:
        Mailer(scraping.log, error=scraping.result)


if __name__ == "__main__":
    main()

