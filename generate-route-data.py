"""
generate-route-data.py

Module for automatically generating a simulated bus route data set.
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

class Route():
    def __init__(self, grid, lon_lat_start, bus_id = None):
        self.grid = grid # For computing paths and distances.
        self.waypoints = [lon_lat_start]
        self.stops = [lon_lat_start]
        self.distance = 0
        self.load = 0
        self.bus_id = bus_id

    def end(self):
        return self.waypoints[-1]

    def stop(self, stop_lon_lat, load = 0):
        end = self.waypoints[-1]
        if not networkx.has_path(self.grid.graph, end, stop_lon_lat):
            return False
        path = networkx.shortest_path(self.grid.graph, end, stop_lon_lat)
        self.waypoints.extend(path[1:])
        self.stops.append(stop_lon_lat)
        self.distance += sum(geopy.distance.vincenty(path[i], path[i+1]).miles for i in range(len(path)-1))
        #self.distance += networkx.shortest_path_length(self.graph, end, stop_lon_lat)
        self.load += load
        return True

    def features(self):
        return [geojson.Feature(geometry=geojson.LineString(self.waypoints), properties={'bus_id': self.bus_id})]

def stops_to_dict(file_json):
    stops = json.load(open(file_json, 'r'))
    return {tuple(map(float, sch.split(','))):{tuple(map(float, stp.split(','))):stops[sch][stp] for stp in stops[sch]} for sch in stops}

def school_to_stops_rtree(stops):
    mapping = {}
    for school in stops:
        school_stops = list(stops[school].items())
        school_rtree = rtree.index.Index()
        for (i, ((lon, lat), count)) in enumerate(school_stops):
            school_rtree.insert(i, (lon, lat, lon, lat))
        mapping[school] = (school_stops, school_rtree)
    return mapping

def school_stops_to_routes(grid, sch_to_stoplist_rtree, buses):
    routes_by_school = {}
    routes = []
    bus_index = 0
    for (sch, (stops, rtree)) in tqdm(list(sch_to_stoplist_rtree.items()), desc='Generating routes'):
        bus = buses[bus_index]
        route = Route(grid, (bus['Bus Longitude'], bus['Bus Latitude']), bus['Bus ID'])
        while True:
            stop_index = next(rtree.nearest(route.end(), 1), None)
            if stop_index is None:
                break
            ((lon, lat), load) = stops[stop_index]
            can_reach_stop = route.stop((lon, lat), load)
            if can_reach_stop:
                rtree.delete(stop_index, (lon, lat, lon, lat))

            # If the stop cannot be reached or the route is becoming too long,
            # finish it and start a new one.
            if (not can_reach_stop) or len(route.stops) > 20 or route.load > 60:
                # Add school and record the route.
                route.stop(sch)
                routes_by_school.setdefault(sch, []).append(route)
                routes.append(route)

                # Start a new route with a new bus.
                bus_index += 1
                if bus_index >= len(buses):
                    break
                
                bus = buses[bus_index]
                route = Route(grid, (bus['Bus Longitude'], bus['Bus Latitude']), bus['Bus ID'])

        # Leave the outer for loop if there are no more buses.
        if bus_index >= len(buses):
            break

    return routes

if __name__ == "__main__":
    grid = Grid('input/segments-prepared.geojson')
    buses = json.load(open('output/buses.json', 'r'))
    stops = stops_to_dict('output/stops.json')
    routes = school_stops_to_routes(grid, school_to_stops_rtree(stops), buses)
    open('output/routes.geojson', 'w').write(geojson.dumps(geojson.FeatureCollection([f for r in routes for f in r.features()])))
    open('output/routes.html', 'w').write(geoleaflet.html(geojson.FeatureCollection([f for r in routes for f in r.features()])))

## eof