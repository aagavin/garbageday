import json
import requests
from cachecontrol import CacheControl

MAP_URL = 'https://map.toronto.ca/geoservices/rest/search/rankedsearch'
GIS_URL = 'https://gis.toronto.ca/arcgis/rest/services/primary/cot_geospatial21_mtm/MapServer/3/query'

query_gis = {
    'geometry': '',
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'returnGeometry': 'false',
    'f': 'pjson'
}

s = requests.session()
c_session = CacheControl(s)


def lambda_handler(event, context):
    address: str = event['address']
    map_r: dict = c_session.get(MAP_URL, params={'searchString': address}).json()
    long, lat = (
        map_r['result']['bestResult'][0]['longitude'],
        map_r['result']['bestResult'][0]['latitude']
    )
    query_gis['geometry'] = f'{long},{lat}'
    gis_r: dict = c_session.get(GIS_URL, params=query_gis).json()
    area_name = gis_r['features'][0]['attributes']['AREA_NAME']
    return area_name.replace(' ', '')
