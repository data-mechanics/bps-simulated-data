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

def students_to_stops(grid, file_students, file_stops, max_dist_miles, max_load):
    students = geojson.load(open(file_students, 'r'))
    stops = {}
    stop_to_load = {}
    for f in tqdm(students.features, desc='Finding stop for each student'):
        coords = f.geometry.coordinates
        (std, sch) = tuple(coords[0]), tuple(coords[-1])

        # Consolidate with an existing stop, if possible.
        stp = None
        if sch in stops:
            for stp_existing in stops[sch]:
                if geopy.distance.vincenty(std, stp_existing).miles <= max_dist_miles and\
                   stops[sch][stp_existing] < max_load:
                    stp = stp_existing
                    break
        if stp is None:
            i = next(grid.rtree_nodes.nearest(std + std, 1), None)      
            stp = tuple(grid.segments['features'][i].coordinates)

        stops.setdefault(sch, {})
        stops[sch].setdefault(stp, 0)
        stops[sch][stp] += 1

        # Update student entry with the stop information.
        f.geometry.coordinates = [coords[0], stp, coords[-1]]

    open(file_students, 'w').write(geojson.dumps(students, indent=2))
    open(file_stops, 'w').write(json.dumps(stops_to_json_compatible(stops), indent=2))
    return (students, stops)

def stops_to_dict(file_json):
    stops = json.load(open(file_json, 'r'))
    school_stop_to_load = {}
    for [sch, stp, load] in stops:
        (sch, stp) = (tuple(sch), tuple(stp))
        if sch not in school_stop_to_load:
            school_stop_to_load[sch] = {}
        if stp not in school_stop_to_load[sch]:
            school_stop_to_load[sch][stp] = load
    return school_stop_to_load

def stops_to_json_compatible(stops):
    '''
    Tuples cannot be keys in a JSON file, so we replace
    them with strings.
    '''
    return [[sch, stp, stops[sch][stp]] for sch in stops for stp in stops[sch]]

if __name__ == "__main__":
    grid = Grid('input/segments-prepared.geojson')
    (students, stops) = students_to_stops(grid, 'output/students.geojson', 'output/stops.json', 0.3, 15)

## eof