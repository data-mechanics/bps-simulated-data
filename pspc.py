"""
pspc.py

Module for building a shortest-path cache.
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

#grid = Grid('input/segments-prepared.geojson')

#Grid.prepare('input/segments-boston.geojson', 'input/segments-small.geojson')
grid = Grid('input/segments-small.geojson')

#for f in grid.segments['features']:
#    if 'geometry' in f and f['geometry']['type'] == 'LineString':
#        f['geometry']['coordinates'] = [f['geometry']['coordinates'][0], f['geometry']['coordinates'][-1]]

nodes = [f for f in grid.segments['features'] if f['type'] == 'Point']
edges = [f for f in grid.segments['features'] if f['type'] != 'Point']
grid.segments['features'] = edges + nodes
print(len(nodes))
node_to_index = {tuple(nodes[i]['coordinates']):i for i in range(len(nodes))}

for node in tqdm(nodes):
    paths = networkx.shortest_path(grid.graph, tuple(node['coordinates']))
    next_to_targets = {}
    for trg in paths:
        if len(paths[trg]) >= 2:
            next = paths[trg][1]
            next_to_targets.setdefault(next, []).append(trg)
    node.setdefault('properties', {}).update({'next':[[node_to_index[n] for n in next_to_targets[next] if n in node_to_index] for next in next_to_targets]})

    #print(set([paths[trg][1] for trg in paths if len(paths[trg]) >= 2]))

#paths = networkx.all_pairs_shortest_path(grid.graph)

#open('view.html', 'w').write(geoleaflet.html(grid.segments)) # Create visualization.

open('pspc.js', 'w').write("var obj = \n"+json.dumps(grid.segments, indent=2, sort_keys=True)+";")

print("End.")

## eof