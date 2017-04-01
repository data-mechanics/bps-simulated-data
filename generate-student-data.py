"""
generate-student-data.py

Module for automatically generating a simulated student data set.
"""

import os
import requests
import random
import math
import json
import geojson
import geopy.distance
import shapely.geometry
from tqdm import tqdm
import xlsxwriter
import rtree

def properties_by_zipcode(file_prefix):
    """
    Build a JSON file grouping all residential properties by zip code
    and assigning the US Census Bureau Census Block numbers (FIPS codes)
    to them.
    """
    # Get the (feature, shape) pairs for each census block.
    block_shapes = [(f, shapely.geometry.shape(f['geometry'])) for f in tqdm(geojson.loads(open('input_data/c_bra_bl.geojson').read())['features']) if f['geometry'] is not None]

    # Build R-tree index for the census block shapes
    # to make it easier to find the block closest to
    # a point.
    rtidx = rtree.index.Index()
    for i in tqdm(range(len(block_shapes))):
        (f, s) = block_shapes[i]
        rtidx.insert(i, s.bounds)

    # Build the dictionary mapping zip codes to all properties
    # in that zip code.
    properties = json.load(open(file_prefix + '.geojson', 'r'))
    boston_zips = {}
    for i in tqdm(properties):
        zipcode = properties[i]['properties']['zipcode']
        address = properties[i]['properties']['address']
        if zipcode != "NULL" and address != "NULL" and properties[i]['properties']['type'] == 'Residential':
            boston_zips.setdefault(zipcode, {})
            boston_zips[zipcode][i] = properties[i]

            # Given the location of a property, loop through all nearby
            # block shapes (according to the R-tree index) and assign
            # the shape's block code to that property.
            (lat, lon) = properties[i]['geometry']['coordinates']
            for (f, s) in [block_shapes[i] for i in rtidx.nearest((lon, lat, lon, lat), 1)]:
                if s.contains(shapely.geometry.Point(lon, lat)):
                    boston_zips[zipcode][i]['geocode'] = f['properties']['CODE']
                    last = (f, s)
                    break
            # The above could alternatively be implemented via API
            # calls to the Census Block Conversions API. However,
            # the service does not use R-tree indices so it's slower.
            #geocode = json.loads(requests.get('http://data.fcc.gov/api/block/find?format=json&latitude=' + str(lat) + '&longitude=' + str(lon) + '&showall=true').text)["Block"]["FIPS"][0:-3]
            #boston_zips[zipcode][i]['geocode'] = geocode

    open(file_prefix + '-by-zipcode.json', 'w').write(json.dumps(boston_zips, indent=2))

def percentages_csv_to_json(file_prefix):
    """
    Reads the student-zip-school-percentages or equivalent file and outputs it
    as a JSON format file.
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

def zip_to_school_to_location(file_prefix, student_zip_school_percentages = 'input_data/student-zip-school-percentages'):
    """
    Reads the school CSV to construct a JSON with schools ordered by zipcode.
    and extended with attendance information based on the percentages data.
    """
    rows = open(file_prefix + '.csv', 'r').read().split("\n")
    fields = rows[0].split("\t")
    rows = [dict(zip(fields, row.split("\t"))) for row in rows[1:]]
    zips = {row['zip'] for row in rows[1:]}

    # Gets attendance data from student_zip_school_percentages.
    zip_student_percentages = json.loads(open(student_zip_school_percentages + '.json', 'r').read())
    # Calculates total number of students in zip_student_percentages.
    total_students = sum([zip_student_percentages[z]['total'] for z in zip_student_percentages])

    zip_to_name_to_loc = {
        zip:{
            r['name'].strip(): {
                'location': (float(r['longitude']), float(r['latitude'])),
                'name': r['name'],
                'address': r['address'],
                'attendance': sum([math.ceil((zip_student_percentages[z]['schools'][r['name']] if r['name'] in zip_student_percentages[z]['schools'] else 0 ) * zip_student_percentages[z]['total']) for z in zip_student_percentages]),
                'attendance_share': sum([math.ceil((zip_student_percentages[z]['schools'][r['name']] if r['name'] in zip_student_percentages[z]['schools'] else 0 ) * zip_student_percentages[z]['total']) for z in zip_student_percentages]) / total_students
              }
            for r in rows[1:] if zip == r['zip']
          }
        for zip in zips
      }
    return school_to_bell_time(zip_to_name_to_loc)

def school_to_bell_time(school_json):
    """
    Takes the school JSON output from zip_to_school_to_location and assigns
    bell times.
    """
    attendance_percents = {'07:30:00':0.0, '08:30:00':0.0, '09:30:00':0.0}
    attendance_thresholds = {'07:30:00':40.0, '08:30:00':40.0, '09:30:00':20.0}
    for zipcode in school_json:
        for schools in school_json[zipcode]:
            while True:
                selected_time = random.choice(['07:30:00', '08:30:00', '09:30:00'])
                if attendance_percents[selected_time] < attendance_thresholds[selected_time]:
                    school_json[zipcode][schools]['start'] = selected_time
                    if selected_time == '07:30:00':
                        school_json[zipcode][schools]['end'] = random.choice(['14:10:00', '15:00:00'])
                    if selected_time == '08:30:00':
                        school_json[zipcode][schools]['end'] = random.choice(['15:10:00', '16:00:00'])
                    if selected_time == '09:30:00':
                        school_json[zipcode][schools]['end'] = random.choice(['16:10:00', '17:00:00'])
                    attendance_percents[selected_time] += school_json[zipcode][schools]['attendance_share']
                    break
    return school_json

def students_simulate(file_prefix_properties, file_prefix_percentages, file_prefix_students):
    """
    Builds and emits a simulated student data set that randomly assigns
    a school (and other characteristics) to every student based on
    appropriate distributions and other criteria.
    """
    neighborhood_safety = json.load(open('input_data/neighborhood-safety.json'))
    grade_safe_distance = json.load(open('input_data/grade-safe-distance.json'))
    props = json.loads(open(file_prefix_properties + '.json', 'r').read())
    percentages = json.loads(open(file_prefix_percentages + '.json', 'r').read())
    schools = zip_to_school_to_location('input_data/schools')
    schools_to_data = {school:schools[zip][school] for zip in schools for school in schools[zip]}
    features = []
    for zip in percentages.keys() & props.keys():
        if zip in schools and len(schools[zip]) > 0:
            for (school, fraction) in tqdm(percentages[zip]['schools'].items()):
                if school in schools_to_data:
                    school_loc = schools_to_data[school]['location']
                    for ty in ['corner', 'd2d']:
                        for student in range(int(1.0 * fraction * percentages[zip][ty])):
                            r = random.randint(10,20)
                            locations = [(geopy.distance.vincenty(tuple(reversed(prop['geometry']['coordinates'])), school_loc).miles, prop) for prop in random.sample(list(props[zip].values()), r)]
                            locations = [(d, p) for (d, p) in locations if d >= 0.65]
                            locations = list(sorted(locations, key=lambda t: t[0]))
                            attempts = 0
                            while len(locations) == 0 and attempts < 100:
                                attempts += 1
                                r = min(len(props[zip].values()), r + 10)
                                locations = [(geopy.distance.vincenty(tuple(reversed(prop['geometry']['coordinates'])), school_loc).miles, prop) for prop in random.sample(list(props[zip].values()), r)]
                                locations = [(d, p) for (d, p) in locations if d >= 0.65]
                                locations = list(sorted(locations, key=lambda t: t[0]))
                            if len(locations) > 0:
                                location = locations[0][1]
                                end = school_loc
                                start = tuple(reversed(location['geometry']['coordinates']))
                                geometry = geojson.Point(start)
                                geometry = geojson.LineString([start, end])

                                grade = random.choice('K123456')
                                geocode = location.get('geocode')
                                geocode = geocode[0:-4] if geocode is not None else None
                                safety = neighborhood_safety.get(geocode)

                                properties = {
                                    'length':geopy.distance.vincenty(start, end).miles,
                                    'zip':zip,
                                    'pickup':ty,
                                    'grade':grade,
                                    'geocode':geocode,
                                    'safety':safety,
                                    'walk':grade_safe_distance[grade][safety] if safety is not None else None,
                                    'school': schools_to_data[school]['name'],
                                    'school_address': schools_to_data[school]['address'],
                                    'school_start': schools_to_data[school]['start'],
                                    'school_end': schools_to_data[school]['end']
                                  }
                                if type(location['properties']['address']) == str and len(location['properties']['address'].split(" ")) >= 2:
                                    parts = location['properties']['address'].strip().split(" ")
                                    (number, street) = (parts[0], " ".join(parts[1:]))
                                    properties['number'] = number
                                    properties['street'] = street.split("#")[0].strip() # No unit numbers.
                                features.append(geojson.Feature(geometry=geometry, properties=properties))
        else:
            pass
    open(file_prefix_students + '.geojson', 'w').write(geojson.dumps(geojson.FeatureCollection(features), indent=2))
    features = list(reversed(sorted(features, key=lambda f: f['properties']['length'])))
    return geojson.FeatureCollection(features)

def geojson_to_xlsx(geojson_file, xlsx_file):
    """
    Converts a simulated student data set in JSON format into a human-friendly
    Excel format (with appropriate) changes to field/column names.
    """
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
    properties_by_zipcode('input_data/properties')
    percentages_csv_to_json('input_data/student-zip-school-percentages')
    students = students_simulate('input_data/properties-by-zipcode', 'input_data/student-zip-school-percentages', 'students')
    open('visualization.js', 'w').write('var obj = ' + geojson.dumps(students) + ';')
    geojson_to_xlsx('students.geojson', 'students.xlsx')

main()

## eof