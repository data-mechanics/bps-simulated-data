import os
import random
import zipfile
import json
import geojson
import geopy.distance
import shapefile # pyshp library
import pyproj
from tqdm import tqdm
import geoleaflet
import xlsxwriter
import math

#current data directory
os.chdir("./input_data")

def point_in_poly(x, y, poly):
    """
    Determine whether a point is inside a given polygon (list of (x,y) pairs).
    Returns True or False. Uses ray casting (source: geospatialpython.com).
    """
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

def extract_zipcode_data():
    if not os.path.isdir('zipcodes_nt'):
        with zipfile.ZipFile('zipcodes_nt.zip') as f:
            f.extractall("./zipcodes_nt")

# def properties_by_zipcode(file_prefix):
#     """
#     Build a JSON file grouping all properties by zip code.
#     """
#     sf = shapefile.Reader('zipcodes_nt/ZIPCODES_NT_POLY')
#     reverse_coordinate_projection = pyproj.Proj(proj = 'lcc', datum = 'NAD83',
#                                     lat_1 = 41.71666666666667, lat_2 = 42.68333333333333,
#                                     lat_0 = 41.0, lon_0 = -71.5,
#                                     x_0 = 200000.0, y_0 = 750000.0)

#     ZIPFIELD = 0 # Constant for the zipcode field.

#     # Load all residences in Boston.
#     properties = json.load(open('properties.geojson', 'r'))
#     residences = [p for p in properties.items() if p[1]['properties']['type'] == 'Residential']

#     # Convert shapefile to dictionary one time.
#     # The shapefile actually does not contain unique zipcode data so we have to make sure to have multipolygons.
#     # For now, just ignore the list.
#     blacklist = ['01434', '01082', '02532', '01002', '01039', '01050', '02467', '01096', '01026', '01011', '01247', '01010', '01235', '01008']

#     zipcode_polygons = {}
#     for sr in sf.iterShapeRecords():
#         zc = sr.record[ZIPFIELD] # zip code
#         if zc in blacklist:
#             continue # FIX THIS
#         polygon = []
#         for x,y in sr.shape.points:
#             lng, lat = reverse_coordinate_projection(x, y, inverse=True)
#             polygon.append((lat, lng))
#         zipcode_polygons[zc] = polygon

#     # Map a list of residences to their zip codes.
#     zipcodes = {zc:[] for zc in zipcode_polygons}
#     for k, residence in tqdm(residences):
#         res_lat, res_lng = residence['geometry']['coordinates']
#         for zc, polygon in zipcode_polygons.items():
#             if point_in_poly(res_lat, res_lng, polygon):
#                 zipcodes[zc].append((k, residence))
#                 break

#     with open(file_prefix + '.json', 'w') as f:
#         f.write(json.dumps(zipcodes))

def properties_by_zipcode(file_prefix):
    """
    Build a JSON file grouping all residential properties by zip code
    """

    boston_zips = {}

    properties = json.load(open(file_prefix + '.geojson', 'r'))

    for i in properties:
        zipcode = properties[i]['properties']['zipcode']
        if zipcode != "NULL" and properties[i]['properties']['type'] == 'Residential':
            if zipcode in boston_zips:
                boston_zips[zipcode][i] = properties[i]
            else:
                boston_zips[zipcode] = {}
                boston_zips[zipcode][i] = properties[i]
        else:
            pass

    txt = json.dumps(boston_zips, indent=2)
    open(file_prefix + '-by-zipcode.json', 'w').write(txt)

def percentages_csv_to_json(file_prefix):
    """
    Reads the student-zip-school-percentages or equivalent file and outputs it as a json
    """
    rows = open(file_prefix + '.csv', 'r').read().split("\n")
    fields = rows[0].split("\t")
    rows = [list(zip(fields, row.split("\t"))) for row in tqdm(rows[1:])]
    zip_to_percentages = {}
    for r in rows:
        zip_to_percentages[r[0][1]] = {
            'corner': int(r[1][1]),
            'd2d': int(r[2][1]),
            'total': int(r[3][1]),
            'schools': dict([(f,float(v)) for (f,v) in r[4:] if float(v) > 0])
          }
    txt = json.dumps(zip_to_percentages, indent=2)
    open(file_prefix + '.json', 'w').write(txt)

def zip_to_school_to_location(file_prefix, school_names_bps_to_cob = 'school-names-bps-to-cob', student_zip_school_percentages = 'student-zip-school-percentages'):
    """
    Reads the school csv to construct a json with schools ordered by zipcode with BPS and Cob names plus attendance based on the percentages_csv_to_json output data
    """
    rows = open(file_prefix + '.csv', 'r').read().split("\n")
    fields = rows[0].split("\t")
    rows = [dict(zip(fields, row.split("\t"))) for row in rows[1:]]
    zips = {row['zip'] for row in rows[1:]}

    # Gets school names necessary to go back and forth between BPS and Cob
    bps_to_cob = json.loads(open(school_names_bps_to_cob + '.json', 'r').read())
    # Gets attendance data from student_zip_school_percentages
    zip_student_percentages = json.loads(open(student_zip_school_percentages + '.json', 'r').read())
    # Calculates total number of students in zip_student_percentages
    total_students = sum([zip_student_percentages[z]['total'] for z in zip_student_percentages])

    zip_to_name_to_loc = {
        zip:{
            r['name'].strip(): {
                'location': (float(r['longitude']), float(r['latitude'])),
                'name': r['name'],
                'name_cob': (bps_to_cob[r['name']] if r['name'] in bps_to_cob else r['name']),
                'address': r['address'],
                'start': random.choice(['07:30:00', '08:30:00', '09:30:00']),
                'end': random.choice(['14:10:00', '15:00:00', '15:10:00', '16:00:00', '16:10:00', '17:00:00']),
                'attendance': sum([math.ceil((zip_student_percentages[z]['schools'][r['name']] if r['name'] in zip_student_percentages[z]['schools'] else 0 ) * zip_student_percentages[z]['total']) for z in zip_student_percentages]),
                'attendance_share': sum([math.ceil((zip_student_percentages[z]['schools'][r['name']] if r['name'] in zip_student_percentages[z]['schools'] else 0 ) * zip_student_percentages[z]['total']) for z in zip_student_percentages]) / total_students
              }
            for r in rows[1:] if zip == r['zip']
          }
        for zip in zips
      }
    return zip_to_name_to_loc

def school_to_bell_time():
    """
    Takes the school JSON output from zip_to_school_to_location and assigns bell times.
    """

    school_json = zip_to_school_to_location(schools)

    attendance_percents = {'07:30:00':0.0, '08:30:00':0.0, '09:30:00':0.0}
    attendance_thresholds = {'07:30:00':40.0, '08:30:00':40.0, '09:30:00':20.0}

    for zip in school_json:
        for schools in zip:
            while True:
                selected_time = random.choice(['07:30:00', '08:30:00', '9:30:00'])
                if attendance_percents[selected_time] < attendance_thresholds[selected_time]:
                    schools['start'] = selected_time
                    attendance_percents[selected_time] += schools[attendance_share]
                    break
    return school_json

def students_simulate(file_prefix_properties, file_prefix_percentages, file_prefix_students):
    """
    Reads the properties_by_zip, student-zip-school-percentages to output the generated data
    """

    props = json.loads(open(file_prefix_properties + '.json', 'r').read())
    percentages = json.loads(open(file_prefix_percentages + '.json', 'r').read())
    schools = zip_to_school_to_location('schools')
    schools_to_data = {school:schools[zip][school] for zip in schools for school in schools[zip]}
    features = []
    for zip in percentages.keys() & props.keys():
        if zip in schools and len(schools[zip]) > 0:
            for (school, fraction) in tqdm(percentages[zip]['schools'].items()):
                if school in schools_to_data:
                    school_loc = schools_to_data[school]['location']
                    for ty in ['corner', 'd2d']:
                        for student in range(int(1.0 * fraction * percentages[zip][ty])):
                            r = random.randint(1,5)
                            locations = list(sorted([(geopy.distance.vincenty(tuple(reversed(prop['geometry']['coordinates'])), school_loc).miles, prop) for prop in random.sample(list(props[zip].values()), r)], key=lambda t: t[0]))
                            location = locations[0][1]
                            end = school_loc
                            start = tuple(reversed(location['geometry']['coordinates']))
                            geometry = geojson.Point(start)
                            geometry = geojson.LineString([start, end])
                            properties = {
                              'length':geopy.distance.vincenty(start, end).miles,
                              'pickup':ty,
                              'grade':random.choice('K123456'),
                              'zip':zip,
                              'school': schools_to_data[school]['name'],
                              'school_address': schools_to_data[school]['address'],
                              'school_start': schools_to_data[school]['start'],
                              'school_end': schools_to_data[school]['end']
                            }
                            features.append(geojson.Feature(geometry=geometry, properties=properties))
        else:
            pass #print(zip)
    open(file_prefix_students + '.geojson', 'w').write(geojson.dumps(geojson.FeatureCollection(features), indent=2))
    features = list(reversed(sorted(features, key=lambda f: f['properties']['length'])))
    return geojson.FeatureCollection(features)

def geojson_to_xlsx(geojson_file, xlsx_file):
    '''
    Converts a JSON file into an XLSX file.
    '''
    xl_workbook = xlsxwriter.Workbook(xlsx_file)
    xl_bold = xl_workbook.add_format({'bold': True})
    xl_sheet = xl_workbook.add_worksheet("Student Information")
    columns = [
        ('Street Number', lambda f: f['properties'].get('number')),
        ('Street Name', lambda f: f['properties'].get('street')),
        ('Zip Code', lambda f: f['properties'].get('zip')),
        ('Latitude', lambda f: float(f['geometry']['coordinates'][0][0])),
        ('Longitude', lambda f: float(f['geometry']['coordinates'][0][1])),
        ('Pickup Type', lambda f: f['properties'].get('pickup')),
        ('Grade', lambda f: f['properties'].get('grade')),
        ('Geocode', lambda f: f['properties'].get('geocode')),
        ('Neighborhood Safety Score', lambda f: f['properties'].get('safety')),
        ('Proposed Maximium Walk to Stop Distance', lambda f: f['properties'].get('walk')),
        ('Assigned School', lambda f: f['properties'].get('school')),
        ('Current School Start Time', lambda f: f['properties'].get('school_start')),
        ('Current School End Time', lambda f: f['properties'].get('school_end')),
        ('School Address', lambda f: f['properties'].get('school_address')),
        ('School Latitude', lambda f: float(f['geometry']['coordinates'][1][0])),
        ('School Longitude', lambda f: float(f['geometry']['coordinates'][1][1]))
      ]
    features = json.loads(open(geojson_file).read())['features']
    for i in range(0, len(columns)):
        xl_sheet.write(0, i, columns[i][0], xl_bold)
    for i in tqdm(range(len(features))):
        for j in range(0,len(columns)):
            xl_sheet.write(i+1, j, columns[j][1](features[i]))
    xl_workbook.close()

def main():
    #extract_zipcode_data()
    #properties_by_zipcode('properties-by-zipcode')
    percentages_csv_to_json('student-zip-school-percentages')
    students = students_simulate('properties-by-zipcode', 'student-zip-school-percentages', 'students')
    open('visualization.js', 'w').write('var obj = ' + geojson.dumps(students) + ';')
    geojson_to_xlsx('students.geojson', 'students.xlsx')

main()

## eof
