"""
generate-assembled-data.py

Module for automatically assembling a comprehensive XLSX workbook containing all
the generated data (assuming the other data sets have already been individually
generated).
"""

import json
import geojson
import xlsxwriter
from tqdm import tqdm

def assemble_sheet_buses(xl_workbook, xl_bold, file_buses_json):
    xl_sheet_buses = xl_workbook.add_worksheet("Buses")
    columns = [
        ('Bus Capacity', lambda b: int(b['Bus Capacity'])),
        ('Bus ID', lambda b: b['Bus ID']),
        ('Bus Latitude', lambda b: float(b['Bus Latitude'])),
        ('Bus Longitude', lambda b: float(b['Bus Longitude'])),
        ('Bus Type', lambda b: b['Bus Type']),
        ('Bus Yard', lambda b: b['Bus Yard']),
        ('Bus Yard Address', lambda b: b['Bus Yard Address'])
      ]
    buses = json.load(open(file_buses_json, 'r'))
    for i in range(0, len(columns)):
        xl_sheet_buses.write(0, i, columns[i][0], xl_bold)
    for i in tqdm(range(len(buses)), desc="Converting JSON bus entries to XLSX rows (Buses)"):
        for j in range(0,len(columns)):
            xl_sheet_buses.write(i+1, j, columns[j][1](buses[i]))

def assemble_sheet_assignments(xl_workbook, xl_bold, file_students_geojson):
    xl_sheet_assignments = xl_workbook.add_worksheet("Stop-Assignments")
    columns = [
        ('Student Latitude', lambda f: float(f['geometry']['coordinates'][0][0])),
        ('Student Longitude', lambda f: float(f['geometry']['coordinates'][0][1])),
        ('Pickup Type', lambda f: f['properties'].get('pickup')),
        ('Grade', lambda f: f['properties'].get('grade')),
        ('Proposed Maximium Walk to Stop Distance', lambda f: f['properties'].get('walk')),
        ('Current School Start Time', lambda f: f['properties'].get('school_start')),
        ('Current School End Time', lambda f: f['properties'].get('school_end')),
        ('School Latitude', lambda f: float(f['geometry']['coordinates'][-1][0])),
        ('School Longitude', lambda f: float(f['geometry']['coordinates'][-1][1])),
        ('Stop Latitude', lambda f: float(f['geometry']['coordinates'][1][0])),
        ('Stop Longitude', lambda f: float(f['geometry']['coordinates'][1][1]))
      ]
    features = json.load(open(file_students_geojson, 'r'))['features']
    for i in range(0, len(columns)):
        xl_sheet_assignments.write(0, i, columns[i][0], xl_bold)
    for i in tqdm(range(len(features)), desc="Converting GeoJSON features to XLSX rows (Stop-Assignments)"):
        for j in range(0,len(columns)):
            xl_sheet_assignments.write(i+1, j, columns[j][1](features[i]))

def assemble_sheet_routes(xl_workbook, xl_bold, file_routes_geojson):
    xl_sheet_assignments = xl_workbook.add_worksheet("Routes")
    columns = [
        ('Bus ID', lambda e: e[2]),
        ('Waypoint Latitude', lambda e: e[1]),
        ('Waypoint Longitude', lambda e: e[0])
        #('Waypoint Address', lambda e: e[3])
      ]
    rs = geojson.load(open(file_routes_geojson, 'r'))
    entries = [[p[0], p[1], f['properties']['bus_id'], '?'] for f in rs.features for p in f['geometry']['coordinates']]
    for i in range(0, len(columns)):
        xl_sheet_assignments.write(0, i, columns[i][0], xl_bold)
    for i in tqdm(range(len(entries)), desc="Converting GeoJSON coordinates to XLSX rows (Routes)"):
        for j in range(0,len(columns)):
            xl_sheet_assignments.write(i+1, j, columns[j][1](entries[i]))

def assemble_xlsx(file_buses_json, file_students_geojson, file_routes_geojson, file_assembled_xlsx):
    '''
    Converts a simulated student data set in JSON format into a human-friendly
    Excel format (with appropriate) changes to field/column names.
    '''
    xl_workbook = xlsxwriter.Workbook(file_assembled_xlsx)
    xl_bold = xl_workbook.add_format({'bold': True})
    assemble_sheet_buses(xl_workbook, xl_bold, file_buses_json)
    assemble_sheet_assignments(xl_workbook, xl_bold, file_students_geojson)
    assemble_sheet_routes(xl_workbook, xl_bold, file_routes_geojson)
    xl_workbook.close()

if __name__ == "__main__":
    assemble_xlsx(
        'output/buses.json',
        'output/students.geojson',
        'output/routes.geojson',
        'output/assembled.xlsx'
      )

## eof