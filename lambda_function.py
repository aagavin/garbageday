import csv
import os
import smtplib
import ssl
import datetime
from io import StringIO
from email.message import EmailMessage

import httpx

MAP_URL = 'https://map.toronto.ca/geoservices/rest/search/rankedsearch'
GIS_URL = 'https://gis.toronto.ca/arcgis/rest/services/primary/cot_geospatial21_mtm/MapServer/3/query'
SHEET_URL = 'https://ckan0.cf.opendata.inter.prod-toronto.ca/download_resource/6686b0d0-afa3-4d2e-be2b-5fe37bde7872?format=csv'
NO_RESULTS_ERROR = 'No results found'
session = httpx.Client()

SMPT_PORT = 465  # For SSL
SMPT_USERNAME = os.getenv('SMPT_USERNAME')
SMPT_FROM = os.getenv('SMPT_FROM')
SMPT_TO = os.getenv('SMPT_TO')
SMPT_PASS = os.getenv('SMPT_PASS')
SMPT_DOMAIN = os.getenv('SMPT_DOMAIN')
SMPT_CONTEXT = ssl.create_default_context()

query_gis = {
    'geometry': '',
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'returnGeometry': 'false',
    'f': 'pjson'
}


def get_collection_schedule(event) -> tuple:
    address: str = event['address']
    map_r: dict = session.get(MAP_URL, params={'searchString': address}).json()
    if map_r['result']['bestResult']:
        long, lat = (
            map_r['result']['bestResult'][0]['longitude'],
            map_r['result']['bestResult'][0]['latitude']
        )
    else:
        long, lat = (
            map_r['result']['restOfResults'][0]['longitude'],
            map_r['result']['restOfResults'][0]['latitude']
        )
    query_gis['geometry'] = f'{long},{lat}'
    gis_r: dict = session.get(GIS_URL, params=query_gis).json()
    area_date = gis_r['features'][0]['attributes']['AREA_NAME'].replace(' ', '')
    date = datetime.datetime.now().date()
    gsheet = session.get(SHEET_URL, follow_redirects=True).text
    csv_dict: csv.DictReader = csv.DictReader(StringIO(gsheet))
    for row in csv_dict:
        # >= date.strftime('%Y/%m/%d')[8:]:
        if row["Calendar"] == area_date:
            if row['WeekStarting'][:7] == date.strftime('%Y-%m-%d')[:7] and row['WeekStarting'][8:] > date.strftime('%Y-%m-%d')[8:]:
                return row, csv_dict.__next__()
    return ()


def get_message_str(next_day) -> str:
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


def lambda_handler(event, context):
    schedule: tuple = get_collection_schedule(event)
    if not schedule:
        print(NO_RESULTS_ERROR)
        raise ValueError(NO_RESULTS_ERROR)
    
    message = get_message_str(schedule[0])
    
    email = EmailMessage()
    email.set_content(message)
    email['From'] = SMPT_FROM
    email['TO'] = SMPT_TO

    with smtplib.SMTP_SSL(SMPT_DOMAIN, SMPT_PORT, context=SMPT_CONTEXT) as server:
        server.login(SMPT_USERNAME, SMPT_PASS)
        mail = server.send_message(email)
    return f'result successfully sent {message}'
