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
    stops_old_to_new = {}
    for school in tqdm(schools_to_stops, desc='Consolidating bus stops'):
        stops_new = []
        for (stop, load) in schools_to_stops[school].items():
            consolidated = False
            for i in range(len(stops_new)):
                (stop_new, load_new) = stops_new[i]
                #if geopy.distance.vincenty(stop, stop_new).miles <= max_dist_miles and\
                #   load_new + load <= max_load:
                #    stops_new[i] = (stop_new, load_new + load)
                #    stops_old_to_new[stop] = stop_new
                #    consolidated = True
                #    break
            if not consolidated:
                stops_new.append((stop, load))

        schools_to_stops[school] = dict(stops_new)

    return (schools_to_stops, stops_old_to_new)

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

    (stops, stops_old_to_new) = stops_consolidate(grid, stops, 0.3, 15)

    for i in tqdm(range(len(students.features)), desc='Updating student data'):
        coords = students.features[i].geometry.coordinates
        if coords[1] in stops_old_to_new:
            students.features[i].geometry.coordinates = [coords[0], stops_old_to_new[coords[1]], coords[2]]
        elif not coords[1] in stops[coords[2]]:
            print("Problem!")

    open(file_students, 'w').write(geojson.dumps(students, indent=2))
    open(file_stops, 'w').write(json.dumps(stops_to_json_compatible(stops), indent=2))
    return (students, stops, stops_old_to_new)

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
    (students, stops, stops_old_to_new) = students_to_stops(grid, 'output/students.geojson', 'output/stops.json')

    for f in tqdm(students.features, desc='Checking'):
        coords = f.geometry.coordinates
        (sch, stp) = (tuple(coords[2]), tuple(coords[1]))
        #print(sch not in [sch for sch2 in stops if stp in stops[sch2]])
        if stp not in stops[sch]:
            print("Stop " + str(stp), str((sch, stp) in stops_old_to_new))

## eof