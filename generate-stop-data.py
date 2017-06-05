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

def stops_consolidate(grid, schools_to_stops, max_dist_miles, max_load):
    for school in tqdm(schools_to_stops, desc='Consolidating bus stops'):
        stops = schools_to_stops[school].items()
        stops_new = []
        for (stop, load) in stops:
            consolidated = False
            for i in range(len(stops_new)):
                (stop_new, load_new) = stops_new[i]
                if geopy.distance.vincenty(stop, stop_new).miles < max_dist_miles and\
                   load_new + load <= max_load:
                    stops_new[i] = (stop_new, load_new + load)
                    consolidated = True
                    break
            if not consolidated:
                stops_new.append((stop, load))
        schools_to_stops[school] = dict(stops_new)
    return schools_to_stops

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

        (key_sch, key_stp) = ((lon_sch, lat_sch), (lon_stp, lat_stp))
        stops.setdefault(key_sch, {})
        stops[key_sch].setdefault(key_stp, 0)
        stops[key_sch][key_stp] += 1

    stops = stops_consolidate(grid, stops, 0.3, 15)

    open(file_students, 'w').write(geojson.dumps(students, indent=2))
    open(file_stops, 'w').write(json.dumps(stops_to_json_compatible(stops), indent=2))
    return stops

def stops_to_json_compatible(stops):
    '''
    Tuples cannot be keys in a JSON file, so we replace
    them with strings.
    '''
    conv = lambda lon_lat: str(lon_lat[0]) + ',' + str(lon_lat[1])
    return {conv(sch):{conv(stp):stops[sch][stp] for stp in stops[sch]} for sch in stops}

if __name__ == "__main__":
    grid = Grid('input/segments-prepared.geojson')
    students_to_stops(grid, 'output/students.geojson', 'output/stops.json')

## eof