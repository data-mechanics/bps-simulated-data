import numpy as np
from sklearn.cluster import KMeans
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

# UNFINISHED
def project_points_to_linestrings(points, linestrings):
    # Todo: Implement rtrees to find line points within certain distance
    linestrings = linestrings_to_adj_list(linestrings)
    tree, tree_keys = rTreeify(linestrings.keys())

    projections = []
    for p in points:
        min_proj = (10000, [0,0])

        for lstr in linestrings:
            segments = lstr.geometry.coordinates
            for i in range(len(segments)-1):
                norm = normal(p1, segments[i], segments[i+1])
                if norm < min_proj[0]:
                    proj = project(p1, segments[i], segments[i+1])
                    min_proj = (norm, proj)

        projections.append(min_proj)

    return projections

# UNFINISHED
def generate_student_stops(student_points, numStops=5000):
    kmeans = KMeans(n_clusters=numStops, random_state=0)
    stops = kmeans.fit(student_points).cluster_centers_
    project_points_to_linestrings(stops, linestrings)
