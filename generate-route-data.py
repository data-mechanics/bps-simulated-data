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
        return [geojson.Feature(geometry=geojson.LineString(self.waypoints), properties={'bus_id': self.bus_id, 'load': self.load})]

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

def school_to_stops(stops):
    mapping = {}
    for school in stops:
        mapping[school] = list(stops[school].items())
    return mapping

def closest(q, ps):
    (c, d) = (ps[0], geopy.distance.vincenty(q, ps[0][0]).miles)
    for p in ps:
        di = geopy.distance.vincenty(q, p[0]).miles
        if di < d:
            (c, d) = (p, di)
    return (c, [p for p in ps if p != c])

def school_stops_to_routes(grid, file_students, sch_to_stoplist, buses, max_dist_miles, max_stops):
    routes_by_school = {}
    routes = []
    school_stop_to_bus = {}
    bus_index = -1
    for (sch, stops) in tqdm(list(sch_to_stoplist.items()), desc='Generating routes'):

        # Build R-tree of stops for this school.
        stops_rtree = rtree.index.Index()
        for (i, ((lon, lat), count)) in enumerate(stops):
            stops_rtree.insert(i, (lon, lat, lon, lat))

        # Start a new route with a new bus.
        bus_index += 1
        if bus_index >= len(buses):
            print('Not enough buses.')
            exit()
        bus = buses[bus_index]
        route = Route(grid, (bus['Bus Longitude'], bus['Bus Latitude']), bus['Bus ID'])

        # Assign a bus route to every stop until none are left.
        while True: # len(stops) > 0
            # (((lon, lat), load), stops) = closest(route.end(), stops)
            stop_index = next(stops_rtree.nearest(route.end(), 1), None)
            if stop_index is None: # No more stops remaining.
                break
            ((lon, lat), load) = stops[stop_index]
            stops_rtree.delete(stop_index, (lon, lat, lon, lat))
            
            # Add the stop to the current route.
            reached_stop = route.stop((lon, lat), load)
            school_stop_to_bus[(sch, (lon, lat))] = bus['Bus ID'] # Record in order to update student records.
            if not reached_stop: # Individual location cannot be reached in segment graph.
                print("Could not reach " + str((lon, lat)) + ".")

            # If there are still stops remaining but the route is becoming too long,
            # finish it and start a new one.
            if len(stops) > 0 and\
               ( route.distance >= max_dist_miles or\
                 len(route.stops) >= max_stops or\
                 route.load >= bus['Bus Capacity'] - 5 ):
                # Add school and record the route.
                route.stop(sch)
                routes_by_school.setdefault(sch, []).append(route)
                routes.append(route)

                # Start a new route with a new bus.
                bus_index += 1
                if bus_index >= len(buses):
                    print('Not enough buses.')
                    exit()
                bus = buses[bus_index]
                route = Route(grid, (bus['Bus Longitude'], bus['Bus Latitude']), bus['Bus ID'])

        # We exited the loop, so finish off the last (still under construction) route.
        route.stop(sch)
        routes_by_school.setdefault(sch, []).append(route)
        routes.append(route)

    # Update the student data with the bus assigned to each student.
    students = geojson.load(open(file_students, 'r'))
    for f in tqdm(students.features, desc='Updating student data with bus assignments'):
        coords = f.geometry.coordinates
        f['properties']['bus_id'] = school_stop_to_bus[(tuple(coords[2]), tuple(coords[1]))]
    open(file_students, 'w').write(geojson.dumps(students, indent=2))

    return routes

if __name__ == "__main__":
    grid = Grid('input/segments-prepared.geojson')
    buses = json.load(open('output/buses.json', 'r'))
    students = geojson.load(open('output/students.geojson', 'r'))
    stops = stops_to_dict('output/stops.json')    
    routes = school_stops_to_routes(grid, 'output/students.geojson', school_to_stops(stops), buses, max_dist_miles=20, max_stops=30)
    open('output/routes.geojson', 'w').write(geojson.dumps(geojson.FeatureCollection([f for r in routes for f in r.features()])))
    open('output/routes.html', 'w').write(geoleaflet.html(geojson.FeatureCollection([f for r in routes for f in r.features()])))

## eof