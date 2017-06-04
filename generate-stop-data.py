"""
generate-stop-data.py

Module for automatically generating a simulated bus stop data set.
"""

import random
import math
import json
import geojson
import geopy.distance
import shapely.geometry
from geoql import geoql
import geoleaflet
import folium
import xlsxwriter
import rtree
import numpy as np
import networkx
from tqdm import tqdm

from grid import Grid # Module local to this project.

def students_to_stops(grid, file_students, file_stops):
    students = geojson.load(open(file_students, 'r'))
    stops = {}
    for f in tqdm(students.features, desc='Finding stop for each student'):
        coords = f.geometry.coordinates
        (lon_std, lat_std) = coords[0]
        (lon_sch, lat_sch) = coords[-1]

        i = next(grid.rtree_nodes.nearest((lon_std,lat_std,lon_std,lat_std), 1))
        (lon_stp, lat_stp) = grid.segments['features'][i].coordinates
        f.geometry.coordinates = [(lon_std,lat_std), (lon_stp,lat_stp), (lon_sch,lat_sch)]

        key_sch = str(lon_sch) + ',' + str(lat_sch)
        key_stp = str(lon_stp) + ',' + str(lat_stp)
        stops.setdefault(key_sch, {})
        stops[key_sch].setdefault(key_stp, 0)
        stops[key_sch][key_stp] += 1

    open(file_students, 'w').write(geojson.dumps(students, indent=2))
    open(file_stops, 'w').write(json.dumps(stops, indent=2))

if __name__ == "__main__":
    grid = Grid('input/segments-prepared.geojson')
    students_to_stops(grid, 'output/students.geojson', 'output/stops.json')

## eof