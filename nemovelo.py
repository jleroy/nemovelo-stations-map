#!/usr/bin/env python3

import os
import json
import requests
from datetime import datetime, UTC


def get_setting_or_exit(var_name):
    setting = os.getenv(var_name, '').strip()
    if not setting:
        print(f'Missing "{var_name}" environment variable.')
        exit(1)
    return setting

# Ecovelo program (e.g. "nemovelo" for Nîmes).
program    = get_setting_or_exit('ECOVELO_PROGRAM')
# GeoJSON output file location.
output     = get_setting_or_exit('OUTPUT_FILENAME')
# User-Agent sent to Ecovelo API.
user_agent = get_setting_or_exit('USER_AGENT')

# Request headers.
headers = {
    'Content-Type': 'application/json',
    'User-Agent': user_agent
}

# Requests parameters.
params = {
    'program': program,
    'limit': '100'
}

# Retrieve data from Ecovelo API.
r = requests.get(
    'https://api.cyclist.ecovelo.mobi/2025_03_24/stations',
    params=params
)

try:
    data = r.json()['data']
except KeyError as e:
    print(f'Invalid JSON response.')
    exit(1)

# Output must be in GeoJSON format (RFC 7946).
#
#{
#    "type": "FeatureCollection",
#    "features": [
#        ...
#        {
#            "type": "Feature",
#            "geometry": {
#                "type": "Point",
#                "coordinates": [
#                    4.35818,
#                    43.8353
#                ]
#            },
#            "properties": {
#                "Station": "Arènes",
#                "Électrifiée": "False",
#                "Nombre d'emplacements": "10",
#                "Emplacements disponibles": "4",
#                "Vélos disponibles": "6",
#                "Notes": ""
#            },
#            "id": "gxMzY"
#        },
#        ...
#    ]
#}
geojson = {
    'type': 'FeatureCollection',
    'features': [],
    'last_updated': datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S%z')
}
for object in data:
    if not object['program'] == program:
        continue

    if not object['object'] == 'station':
        continue

    notes = []
    electrical = object['electrical']
    if electrical:
        notes.append('Cette station est **raccordée** au réseau électrique.')

    # Electric bikes *docks* statistics.
    eb_statistics = object['statistics']['docks']['type']['vae']
    # Total number of electric bikes *docks* in this station.
    total_eb_docks = eb_statistics['total']
    # Number of free electric bikes *docks* in this station.
    free_eb_docks = eb_statistics['free']
    # Number of electric bikes available in this station.
    available_eb = object['statistics']['vehicules']['available']['vae']

    # No free docks left at this station.
    if not free_eb_docks:
        notes.append('Le fait que la station soit pleine ne vous empêche pas '
                'd\'y retourner votre vélo. Il suffit d\'accrocher votre vélo '
                'à un déjà présent, en « caddie ».')

    geojson['features'].append({
        'id': object['id'], # We use upstream station ID as identifier.
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [
                object['position']['longitude'],
                object['position']['latitude']
            ]
        },
        'properties': {
            'station': object['name'],
            'electrified': electrical,
            'docks_total': total_eb_docks,
            'docks_available': free_eb_docks,
            'ebikes_available': available_eb,
            'note': '\r\n'.join(notes)
        }
    })

with open(output, 'w') as f:
    json.dump(geojson, f, indent=4)
