import smtplib
import logging
import utils
import json

from email.message import EmailMessage
from pathlib import Path
from utils import italian_date

PROJECT_ROOT = Path('/path/to/project/')

class Mailer:
    """
    A class with two use cases: 
        1. sending the complete email with the link 
        to download today's paper as well as the previous editions
        2. sending error logs
    """
    ADDRESS_BOOK = PROJECT_ROOT / "system" / "address_book.json"
    CREDENTIALS_DB = PROJECT_ROOT / "system" / "creds.creds"
    ARCHIVE_FOLDER = PROJECT_ROOT / "archives"
    LOG_FOLDER = PROJECT_ROOT / "logs"

    def __init__(self, error=False):
        """
        Build the email and send it with gmail
        If an error has occurred the emails is sent to the admin only
        (for debugging purposes)
        """

        self.log = logging.getLogger(__name__)
        self.token = utils.decrypt_credentials(Mailer.CREDENTIALS_DB)["gmail_token"]
        self.sender, self.recipients = self._fetch_mailing_data()

        self.archives = {'paper one': 'paper1_archive.json', 
                         'paper two': 'paper2_archive.json', 
                         'paper three': 'paper3_archive.json'
                         }

        if error:
            self.recipients = self.sender
            self.log_path = f'{Mailer.LOG_FOLDER}/{italian_date(formatter='_')}.log'
            final_msg = self._setup_email('Vedere il log in allegato.', error_flag=True)
            self.send_email(final_msg)
        else:
            contents = self._build_html_body()
            email = self._setup_email(contents)
            self.send_email(email)

            self.log.info("All done!")

    def send_email(self, email):
        """Send the email"""
        # Connect to Gmail SMTP server
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender, self.token)
                server.send_message(email,
                                    from_addr=self.sender,
                                    to_addrs=self.recipients
                                    )
            self.log.info("Email sent.")
        except Exception as e:
            self.log.error(e)

    def _fetch_mailing_data(self):
        """Fetche sender and recipients from the JSON address book"""
        with open(Mailer.ADDRESS_BOOK, "r") as j:
            address_book = json.load(j)
        
        sender = address_book["sender"]
        recipients = address_book["recipients"]

        self.log.info("Mailing data fetched correctly.")

        return sender, recipients 

    def _build_html_body(self):
        """Build the standard email and return a formatted HTML message"""

        html_body = "<html><body>"

        for paper_name, archive_path in self.archives.items():
            new_edition, old_editions = self._fetch_editions(paper_name, archive_path)
            html_body += f"""
            <div style=\"width:300px; margin:0 auto; text-align:center;\">
            <div style=\"font-size: 24px;\">{new_edition}</div>
            <br>{old_editions}</div>
            <br>
            <hr style="border: none; width: 50%; height: 3px; background: #000;">
            <br>
            """

        html_body += "</body></html>"
        self.log.info("HTML body built correctly.")

        return html_body

    def _setup_email(self, msg_to_send, error_flag=False):
        """Build the final email. Used for the daily emails as well as for the error logs"""
        
        email = EmailMessage()
        email.set_content(msg_to_send)
        email.add_alternative(msg_to_send, subtype='html')
        email["From"] = self.sender

        if not error_flag:             # Builds the standard email
            email["Subject"] = f"I giornali di oggi in esclusiva per i non abbonati, i mangiaufo e i parassiti sociali"
            if len(self.recipients) > 1: 
                email["To"] = ", ".join(self.recipients)
            else:
                email["To"] = self.recipients[0]
            self.log.info("Email set up correctly.")
        else:
            email["Subject"] = f"NewsScraper: si è verificato un errore"
            email["To"] = self.sender
            self.log.info('Sending error email...')
            with open(self.log_path, 'rb') as l:
                email.add_attachment(l.read(),
                                     maintype = 'text',
                                     subtype = 'plain',
                                     filename = self.log_path.replace('logs/', '')
                                     )
        return email

    def _fetch_editions(self, paper_name, archive):
        """Retrieve the links of the new edition as well as the old one 
        from the json archive
        Return two HTML-formatted strings
        """
        with open(Mailer.ARCHIVE_FOLDER / f"{archive}", 'r') as f:
            complete_archive = json.load(f)

        latest_edition_date, latest_edition_link = next(iter(complete_archive[0].items()))
        latest_edition_html = f'<a href="{latest_edition_link}">{paper_name} del {latest_edition_date.replace('-', ' ')}</a>'

        old_editions_html = ""

        # Slicing is needed here because the first item will be the latest edition
        for edition in complete_archive[1:]:
            # Impossible to know the key of each dictionary in advance
            edition_date, link = next(iter(edition.items()))
            old_editions_html += f'<br><a href="{link}">{paper_name} del {edition_date.replace('-', ' ')}</a>'
        
        self.log.info("Old editions fetched.")   
        
        return latest_edition_html, old_editions_html


