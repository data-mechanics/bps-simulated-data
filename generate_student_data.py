import json, os
import shapefile
import pyproj
import zipfile

# Determine if a point is inside a given polygon or not
# Polygon is a list of (x,y) pairs. This function
# returns True or False.  The algorithm is called
# the "Ray Casting Method".
# Taken from geospatialpython.com
def point_in_poly(x,y,poly):
    n = len(poly)
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

#def map_students_to_zipcodes:

if not os.path.isdir('zipcodes_nt'):
    with zipfile.ZipFile('zipcodes_nt.zip') as f:
        f.extractall("./zipcodes_nt")

sf = shapefile.Reader('zipcodes_nt/ZIPCODES_NT_POLY')

# Load all residences in Boston
properties = json.load(open('properties.geojson', 'r'))
residences = [p for p in properties.items() if p[1]['properties']['type'] == 'Residential']



