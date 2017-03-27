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

def load_zipcode_data():
    if not os.path.isdir('zipcodes_nt'):
        with zipfile.ZipFile('zipcodes_nt.zip') as f:
            f.extractall("./zipcodes_nt")


load_zipcode_data()
sf = shapefile.Reader('zipcodes_nt/ZIPCODES_NT_POLY')
reverse_coordinate_projection = pyproj.Proj(proj = 'lcc', datum = 'NAD83',
                                lat_1 = 41.71666666666667, lat_2 = 42.68333333333333,
                                lat_0 = 41.0, lon_0 = -71.5,
                                x_0 = 200000.0, y_0 = 750000.0)

# Define a constant for the zipcode field
ZIPFIELD = 0

# Load all residences in Boston
properties = json.load(open('properties.geojson', 'r'))
residences = [p for p in properties.items() if p[1]['properties']['type'] == 'Residential']

# Convert shapefile to dictionary one time
# The shapefile actually does not contain unique zipcode data
# so we have to make sure to have multipolygons
# For now, just ignore the list:
blacklist = ['01434', '01082', '02532', '01002', '01039', '01050', '02467', '01096', '01026', '01011', '01247', '01010', '01235', '01008']

zipcode_polygons = {}
for sr in sf.iterShapeRecords():
    zc = sr.record[ZIPFIELD] # zip code
    if zc in blacklist: continue # FIX THIS

    polygon = []

    for x, y in sr.shape.points:
        lng, lat = reverse_coordinate_projection(x, y, inverse=True)
        polygon.append((lat, lng))

    
    zipcode_polygons[zc] = polygon

# map a list of residences to its zip code
zipcodes = {zc:[] for zc in zipcode_polygons}
count = 0
for k, residence in residences:
    if count % 1000 == 0:
        print(count)
    res_lat, res_lng = residence['geometry']['coordinates']
    for zc, polygon in zipcode_polygons.items():
        if point_in_poly(res_lat, res_lng, polygon):
            zipcodes[zc].append((k, residence))
            break
    count += 1

with open('zipcodes.json', 'w') as f:
    f.write(json.dumps(zipcodes))
