import numpy as np
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

# write function to convert linestrings into adjacency list
#def linestrings_to_adj_list():

def project_points_to_linestrings(points, linestrings):
	# Todo: Implement rtrees to find line points within certain distance
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

