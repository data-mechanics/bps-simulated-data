import numpy as np
from sklearn.cluster import KMeans
from rtree import index
import pickle
from tqdm import tqdm
import geoql, geojson
from copy import deepcopy

# Want a function that takes as input 
# set of geojson points, set of geojson linestrings

# points is a list of (x, y) coordinates
# linestrings is a list of geojson linestrings representing streets

def project(p1, l1, l2):
    # find projection of p1 onto line between l1 and l2
    p1 = np.array(p1)
    l1 = np.array(l1)
    l2 = np.array(l2)

    line = l2 - l1
    vec = p1 - l1
    return vec.dot(line) / line.dot(line) * line  # Projects vec onto line

def normal(p1, l1, l2):
    p1 = np.array(p1)
    l1 = np.array(l1)
    l2 = np.array(l2)

    proj = project(p1, l1, l2)
    norm = l1 + proj - p1
    return norm.dot(norm)

def linestrings_to_adj_list(linestrings):
    '''converts a list of linestrings into an adjacency list of edges'''
    for lstr in linestrings:
        segments = lstr.geometry.coordinates
        adj_list = {}
        for i in range(len(segments)-1):
            v1, v2 = segments[i], segments[i+1]
            adj_list.set_default(v1, [])
            adj_list.set_default(v2, [])
            adj_list[v1].append(v2)
            adj_list[v2].append(v1)

        return adj_list

def rTreeify(points):
    '''take (x,y) pairs and constructs rTree'''
    tree = index.Index()
    tree_keys = {}
    for i, p in enumerate(points):
        tree_keys[str(i)] = p
        x, y = p[0], p[1]
        tree.insert(i,(x,y,x,y))

    return tree, tree_keys

def coordinate_distance(v,w,p):
    '''find distance of point to line segment'''
    seglen_squared = (v[0] - w[0])**2 + (v[1] - w[1])**2
    #t = max(0, min(1, dot(p - v, w - v) / l2))
    t =  max(0, min(1, ((p[0]-v[0])*(w[0]-v[0]) + (p[1]-v[1])*(w[1]-v[1]))/seglen_squared ))
    #projection = v + t * (w - v)
    projection = (t*(w[0] - v[0])+v[0],t*(w[1] - v[1])+v[1])
    return ((p[0] - projection[0])**2 + (p[1] - projection[1])**2 )**0.5

def points_linestrings_coverage(linestring,points_tree,points_tree_keys,points_dict, r):
    '''Using route from dictionary and the points tree, return list of points_tree_keys that are within distance r of the route'''

    multipoint = linestring['geometry']['coordinates']
    
    intersecting_points = set()

    #for each pair of points, find points within the box of endpoints extended by r
    for j in range(1,len(multipoint)):
        #coordinates of endpoints
        yi, xi = multipoint[j-1]
        yj, xj = multipoint[j]

        result_set = set()
        x_min = min(xi, xj) - r
        x_max = max(xi, xj) + r
        y_min = min(yi, yj) - r
        y_max = max(yi, yj) + r
        
        for i in list(points_tree.intersection((x_min,y_min,x_max,y_max))):
            result_set.add(i)

        #for each point in the intersecting set, determine if it's within distance r of the line:
        
        for i in result_set:
            key = points_tree_keys[str(i)]
            coor = points_dict[key]['geometry']['coordinates']

            if coordinateDistance((xi, yi), (xj, yj), (coor[1], coor[0])) <= r:
                intersecting_points.add(i)

    return intersecting_points

# UNFINISHED
def project_points_to_linestrings(points, linestrings):
    # Todo: Implement rtrees to find line points within certain distance

    projections = []
    for x,y in tqdm(points[:1]):
        p = [y, x]
        lstr_copy = deepcopy(linestrings)
        lstr_copy = geoql.features_keep_within_radius(lstr_copy, p, 0.5, 'miles')
        min_proj = (10000, [0,0])

        for lstr in lstr_copy.features:
            segments = lstr.geometry.coordinates
            for i in range(len(segments)-1):
                norm = normal(p, segments[i], segments[i+1])
                if norm < min_proj[0]:
                    proj = project(p, segments[i], segments[i+1])
                    min_proj = (norm, proj)

        projections.append(min_proj)

    return projections

def load_road_segments(fname):
    linestrings = geojson.loads(open(fname, 'r').read())
    linestrings.features = [seg for seg in tqdm(linestrings.features) if seg.type=='Feature']
    return linestrings

def generate_student_stops(student_points, numStops=5000, loadFrom=None):
    if loadFrom:
        means = pickle.load(open(loadFrom, 'rb'))
    else:
        #load student coordinates from students datafile to list of coordinates
        points = [student_points['features'][i]['geometry']['coordinates'][0] for i in range(len(student_points['features']))]
    
        #generate means
        kmeans = KMeans(n_clusters=numStops, random_state=0)
        means = kmeans.fit(points).cluster_centers_

    #to do: assign each mean to the closest line segment
    #       project mean to the line segment
    #       return projected points
    linestrings = load_road_segments('example_extract_missing.geojson')
    #return means, linestrings
    return project_points_to_linestrings(means, linestrings)

stops = generate_student_stops([], loadFrom='kmeans')