import csv
import os
import smtplib
import ssl
from datetime import datetime, timedelta
from io import StringIO

import requests
from cachecontrol import CacheControl

MAP_URL = 'https://map.toronto.ca/geoservices/rest/search/rankedsearch'
GIS_URL = 'https://gis.toronto.ca/arcgis/rest/services/primary/cot_geospatial21_mtm/MapServer/3/query'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Om0nwrYzeombeuMf-1pMksyG7oaTdXVpN3vR7-qrjdo/export?format=csv'

s = requests.session()
c_session = CacheControl(s)

SMPT_PORT = 465  # For SSL
SMPT_USERNAME = os.getenv('SMPT_USERNAME', '')
SMPT_FROM = os.getenv('SMPT_FROM', '')
SMPT_TO = os.getenv('SMPT_TO', '')
SMPT_PASS = os.getenv('SMPT_PASS', '')
SMPT_CONTEXT = ssl.create_default_context()

query_gis = {
    'geometry': '',
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'returnGeometry': 'false',
    'f': 'pjson'
}

date_map = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
}


def get_end_of_week(area_day) -> str:
    # TODO: Fix to get week of the year instead
    offset = date_map[area_day]
    dt = datetime.now().date()
    start = dt - timedelta(days=dt.weekday())
    if dt.weekday() > offset:
        return (start + timedelta(days=offset + 8)).strftime('%Y/%m/%d')
    return (start + timedelta(days=offset)).strftime('%Y/%m/%d')


def get_collection_schedule(event) -> tuple:
    address: str = event['address']
    map_r: dict = c_session.get(MAP_URL, params={'searchString': address}).json()
    long, lat = (
        map_r['result']['bestResult'][0]['longitude'],
        map_r['result']['bestResult'][0]['latitude']
    )
    query_gis['geometry'] = f'{long},{lat}'
    gis_r: dict = c_session.get(GIS_URL, params=query_gis).json()
    area_date = gis_r['features'][0]['attributes']['AREA_NAME'].replace(' ', '')
    end_week = get_end_of_week(area_date[:-1])
    gsheet = c_session.get(SHEET_URL).text
    csv_dict = csv.DictReader(StringIO(gsheet))
    for row in csv_dict:
        if row["Calendar"] == area_date and row["WeekStarting"] == end_week:
            return row, csv_dict.__next__()
    return ()


# def get_message_str()

def lambda_handler(event, context):
    schedule: tuple = get_collection_schedule(event)
    return ''
    with smtplib.SMTP_SSL('smtp.fastmail.com', SMPT_PORT, context=SMPT_CONTEXT) as server:
        server.login(SMPT_USERNAME, SMPT_PASS)
        server.sendmail(SMPT_FROM, SMPT_TO, 'heelo')
