import os
import smtplib
import ssl
import json
import datetime
from email.message import EmailMessage

NO_RESULTS_ERROR = 'No results found'

SMPT_PORT = 465  # For SSL
SMPT_USERNAME = os.getenv('SMPT_USERNAME')
SMPT_FROM = os.getenv('SMPT_FROM')
SMPT_TO = os.getenv('SMPT_TO')
SMPT_PASS = os.getenv('SMPT_PASS')
SMPT_DOMAIN = os.getenv('SMPT_DOMAIN')
SMPT_CONTEXT = ssl.create_default_context()


def get_collection_schedule(event) -> tuple:
    area_date = event['address']
    date = datetime.datetime.now()
    # gsheet = session.get(SHEET_URL, follow_redirects=True).json()
    sheet = open('pickup-schedule-2023.json')
    json_sheet = json.load(sheet)
    day_list_filtered = [d for d in json_sheet if d['Schedule'] == area_date]

    for row in day_list_filtered:
        parsed_date = datetime.datetime.strptime(row['CollectionDate'], '%Y-%m-%d')
        date_diff = date - parsed_date
        if date_diff.days <= 7:
            return row
        return ()


def get_message_str(next_day) -> str:
    next_day.pop("_id", None)
    day = datetime.datetime.strptime(next_day['CollectionDate'], '%Y-%m-%d').strftime('%A, %b %d')
    collection_items = ''.join(
        key + '\n'
        for key, value in next_day.items()
        if len(value) == 1 and value != '0'
    )

    return f"""

Garbage day is on {day}
Items Collected:
{collection_items}"""


def lambda_handler(user: dict):
    schedule: tuple = get_collection_schedule(user)
    if not schedule:
        print(NO_RESULTS_ERROR)
        raise ValueError(NO_RESULTS_ERROR)
    
    message = get_message_str(schedule)
    
    email = EmailMessage()
    email.set_content(message)
    email['From'] = SMPT_FROM
    email['TO'] = SMPT_TO

    with smtplib.SMTP_SSL(SMPT_DOMAIN, SMPT_PORT, context=SMPT_CONTEXT) as server:
        server.login(SMPT_USERNAME, SMPT_PASS)
        mail = server.send_message(email)
    return f'result successfully sent {message}'


if __name__ == "__main__":
    user = {
        "address": os.environ['ADDRESS']
    }
    lambda_handler(user)
