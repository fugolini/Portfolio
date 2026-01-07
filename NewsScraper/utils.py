from datetime import date, timedelta
import locale
import json
from cryptography.fernet import Fernet

def italian_date(which_day=0, formatter=' '):
    """Accept any day (past or future, to the limit of a C int) 
    and convert it into a legible Italian date 
    formatted as number[separator]month[separator]year 
    (e.g. 'Domenica 26 settembre 2082')
    """
    # Localization service (to have the date string in Italian)
    locale.setlocale(locale.LC_TIME, "it_IT")

    day_today = date.today()

    if which_day == 0:
        day_to_return = day_today
    else:
        # -1 = yesterday and +1 = tomorrow 
        day_to_return = day_today + timedelta(days=which_day) 
    
    # Build the date string
    day_of_the_month = day_to_return.strftime("%-d")
    month_today = day_to_return.strftime("%B").lower()
    year_today = day_to_return.strftime("%Y")
    formatted_day = f"{day_of_the_month}{formatter}{month_today}{formatter}{year_today}"
    
    return formatted_day


def encrypt_credentials(credentials, file_path):
    """Encrypt n credentials (passed as a dictionary in the form
    credential: content) 
    and store them in a given file
    Return the encryption key
    """
    
    key_gen = Fernet.generate_key()
    cipher = Fernet(key_gen)

    credentials_dict = {}

    for credential in credentials.keys():
        # Nota bene: Fernet requires bytes, hence the encode() method
        encrypted = cipher.encrypt(credentials[credential].encode())
        # Nota bene: json cannot store bytes, hence the decode() method
        credentials_dict[credential] = encrypted.decode()

    with open(file_path, 'r') as f:
        contents = json.load(f)

    contents['credentials'] = credentials_dict

    with open(file_path, 'w') as f:
        json.dump(contents, f)

    # Save the new key to a file
    store_key(key_gen)


def store_key(key):
    """Store the encrypted key in a .key file"""
    with open('key.key', 'wb') as f:
        # NOTE: The Fernet key is a bytes object, hence the 'b' in 'wb'
        f.write(key)


def retrieve_key():
    """Retrieve the key from a .key file"""
    with open('key.key', 'rb') as f: 
        key = f.read()
    return key


def decrypt_credentials(file_path):
    """Decrypt credentials and return them in a dictionary"""
    key_gen = retrieve_key()
    cipher = Fernet(key_gen)
    decrypted_dict = {}

    with open(file_path, 'r') as f:
        credentials = json.load(f)

    for key, encrypted_value in credentials['credentials'].items():
        # The value must be converted back into bytes because Fernet does not read strings
        encrypted_bytes = encrypted_value.encode()
        decrypted_credential = cipher.decrypt(encrypted_bytes).decode()
        decrypted_dict[key] = decrypted_credential

    return decrypted_dict


def print_address_book():
    """Print the address book"""
    print("\n*** Recipients ***\n")
    with open('address_book.json', 'r') as a:
        address_book = json.load(a)
    i = 1
    for recipient in address_book['recipients']:
        print(f'{i}. {recipient}')
        i += 1
    print('\n')


def add_recipient(recipient):
    """Add a recipient to the address book"""
    with open('address_book.json', 'r') as a:
        address_book = json.load(a)

    address_book['recipients'].append(recipient)
    
    with open('address_book.json', 'w') as a:
        json.dump(address_book, a)
    
    print(f"{recipient} has been added to the address book.\n")


def remove_recipient(recipient):
    """Remove a recipient from the address_books"""
    with open('address_book.json', 'r') as a:
        address_book = json.load(a)

    if recipient in address_book['recipients']:
        address_book['recipients'].remove(recipient)
        with open('address_book.json', 'w') as a:
            json.dump(address_book, a)
        print(f'{recipient} was removed from the address book.\n')
    else:
        print(f'{recipient} is not in the address book.\n')


def write_log(log):
    """Save the log to a file"""
    today = italian_date(formatter='_')
    log_path = f'logs/{today}.log'

    with open(log_path, 'w') as l:
        l.write(log)

    # Return log_path for debugging purposes
    return log_path

