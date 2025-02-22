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


def get_collection_schedule(area_date) -> tuple:
    date = datetime.datetime.now()
    # update the sheet from here
    # https://open.toronto.ca/dataset/solid-waste-pickup-schedule/
    sheet = open('pickup-schedule-2025.json')
    json_sheet = json.load(sheet)
    day_list_filtered = [d for d in json_sheet if d['Calendar'] == area_date]

    for row in day_list_filtered:
        parsed_date = datetime.datetime.strptime(row['WeekStarting'], '%Y-%m-%d')
        date_diff = date - parsed_date
        if parsed_date > date and date_diff.days <= 7:
            return row
    return ()


def get_message_str(next_day: dict) -> str:
    next_day.pop("_id", None)
    day = datetime.datetime.strptime(next_day['WeekStarting'], '%Y-%m-%d').strftime('%A, %b %d')
    collection_items = ''.join(
        key + '\n'
        for key, value in next_day.items()
        if len(value) == 1 and value != '0'
    )

    return f"""

Garbage day is on {day}
Items Collected:
{collection_items}"""


if __name__ == "__main__":
    address = os.environ['ADDRESS']
    schedule: tuple = get_collection_schedule(address)
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
        server.send_message(email)
    print(f'result successfully sent {message}')
