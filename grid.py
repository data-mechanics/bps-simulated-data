"""
grid.py

Module containing class for working with a street grid.
"""

import os.path
import pickle
import json
import geojson
import geopy.distance
import shapely.geometry
from geoql import geoql
import geoleaflet
import folium
import rtree
import networkx
from tqdm import tqdm

class Grid():
    @staticmethod
    def prepare(file_segments, file_segments_filtered):
        '''
        Prepare a "clean" segments file given an input segments file.
        '''
        segments = geoql.load(open(file_segments, 'r'))
        features = []
        for f in tqdm(segments.features, desc='Filtering road segments'):
            if f.type == 'Feature':
                f.properties = []
                features.append(f)
        segments.features = features
        segments = segments.node_edge_graph()
        segments.dump(open(file_segments_filtered, 'w'), sort_keys=True)

    @staticmethod
    def segments_networkx(segments):
        '''
        Convert a GeoJSON graph generated by the geoql function
        node_edge_graph() into a networkx representation.
        '''
        graph = networkx.Graph()
        for (j, feature) in tqdm(list(enumerate(segments['features'])), desc='Building segments graph'):
            if feature.type == "Point":
                (lon, lat) = feature.coordinates
                graph.add_node((lon, lat))
            elif feature.type == "Feature":
                coords = [tuple(c) for c in feature.geometry.coordinates]
                for i in range(len(coords)-1):
                    (s, t) = (coords[i], coords[i+1])
                    graph.add_edge(s, t, index=j, distance=geopy.distance.vincenty(s, t).miles)
        return graph

    @staticmethod
    def segments_rtree(segments):
        '''
        Build an R-tree using the GeoJSON road segments data. Separate
        trees are built for nodes and for edges.
        '''
        (nodes_rtree, edges_rtree) = (rtree.index.Index(), rtree.index.Index())
        for i in tqdm(range(len(segments['features'])), desc='Building segments R-tree'):
            feature = segments['features'][i]
            if feature.type == 'Point':
                (lon, lat) = feature.coordinates
                nodes_rtree.insert(i, (lon, lat, lon, lat))
            elif feature.type == 'Feature':
                edges_rtree.insert(i, shapely.geometry.shape(feature['geometry']).bounds)
        return (nodes_rtree, edges_rtree)

    def __init__(self, file_path, file_pickle = None):
        # Unpickle if a file exists (if it does not, the generated data will
        # be pickled once generated).
        if file_pickle is not None and os.path.isfile(file_pickle):
            obj = pickle.load(open(file_pickle, 'rb'))
            self.segments = obj.segments
            self.graph = obj.graph
            self.rtree_nodes = obj.rtree_nodes
            self.rtree_edges = obj.rtree_edges
            return

        self.segments = geojson.load(open(file_path, 'r'))
        self.graph = self.segments_networkx(self.segments)
        (rtree_nodes, rtree_edges) = self.segments_rtree(self.segments)
        self.rtree_nodes = rtree_nodes
        self.rtree_edges = rtree_edges

        # Pickle the data if a path is specified.
        if file_pickle is not None:
            pickle.dump(self, open(file_pickle, 'wb'))

if __name__ == "__main__":
    # The following is used to generate the "prepared" road segment data.
    Grid.prepare('input/segments-boston.geojson', 'input/segments-prepared.geojson')
    #open('output/segments.html', 'w').write(geoleaflet.html(Grid('input/segments-prepared.geojson').segments))

## eof