import csv
import requests
from io import StringIO
from datetime import datetime, timedelta
from cachecontrol import CacheControl

MAP_URL = 'https://map.toronto.ca/geoservices/rest/search/rankedsearch'
GIS_URL = 'https://gis.toronto.ca/arcgis/rest/services/primary/cot_geospatial21_mtm/MapServer/3/query'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Om0nwrYzeombeuMf-1pMksyG7oaTdXVpN3vR7-qrjdo/export?format=csv'

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

s = requests.session()
c_session = CacheControl(s)


def get_end_of_week(area_day):
    offset = date_map[area_day]
    dt = datetime.now().date()
    start = dt - timedelta(days=dt.weekday())
    return (start + timedelta(days=offset)).strftime('%Y/%m/%d')


def lambda_handler(event, context):
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
            val_tuple = row, csv_dict.__next__()
    val_tuple
    return ''
