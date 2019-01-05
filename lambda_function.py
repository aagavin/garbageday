import csv
import os
import smtplib
import ssl
import datetime
from io import StringIO

import requests

MAP_URL = 'https://map.toronto.ca/geoservices/rest/search/rankedsearch'
GIS_URL = 'https://gis.toronto.ca/arcgis/rest/services/primary/cot_geospatial21_mtm/MapServer/3/query'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Om0nwrYzeombeuMf-1pMksyG7oaTdXVpN3vR7-qrjdo/export?format=csv'

session = requests.session()

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
    long, lat = (
        map_r['result']['bestResult'][0]['longitude'],
        map_r['result']['bestResult'][0]['latitude']
    )
    query_gis['geometry'] = f'{long},{lat}'
    gis_r: dict = session.get(GIS_URL, params=query_gis).json()
    area_date = gis_r['features'][0]['attributes']['AREA_NAME'].replace(' ', '')
    end_week = datetime.datetime.now().date().isocalendar()
    index = 1
    gsheet = session.get(SHEET_URL).text
    csv_dict = csv.DictReader(StringIO(gsheet))
    for row in csv_dict:
        if row["Calendar"] == area_date:
            if end_week[1] == index and int(row['WeekStarting'][:4]) == end_week[0]:
                return row, csv_dict.__next__()
            elif row['WeekStarting'][:4] == end_week[0]:
                index = index + 1
    return ()


def get_message_str(next_two: tuple) -> str:
    return ''


def lambda_handler(event, context):
    schedule: tuple = get_collection_schedule(event)
    with smtplib.SMTP_SSL('smtp.fastmail.com', SMPT_PORT, context=SMPT_CONTEXT) as server:
        server.login(SMPT_USERNAME, SMPT_PASS)
        server.sendmail(SMPT_FROM, SMPT_TO, 'heelo')
