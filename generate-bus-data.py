"""
generate-bus-data.py

Module for automatically generating a simulated bus data set.
"""

import os
import json
import xlrd
from tqdm import tqdm

from grid import Grid # Module local to this project.

def str_ascii_only(s):
    '''
    Convert a string to ASCII and strip it of whitespace pre-/suffix.
    '''
    return s.encode("ascii", errors='ignore').decode("ascii").strip()

def xlsx_cell_to_json(column, cell):
    '''
    Use appropriate data structures and string representations
    based on the column/field and cell value.
    '''
    cell_type = xlrd.sheet.ctype_text.get(cell.ctype, 'unknown type')
    if cell_type == 'empty':
        return None
    elif cell_type == 'number' and abs(cell.value - int(cell.value)) < 0.0000000001:
        return int(cell.value)
    elif cell_type == 'number':
        return float(cell.value)
    elif cell_type == 'text':
        return str_ascii_only(str(cell.value))
    return None

def xlsx_to_json(file_xlsx, file_json):
    '''
    Converts a bus data XLSX spreadsheet into a JSON file.
    '''
    xl_workbook = xlrd.open_workbook(file_xlsx)
    xl_sheet = xl_workbook.sheet_by_index(0)
    row = xl_sheet.row(0)
    cols = [cell_obj.value for idx, cell_obj in enumerate(row)]
    entries = []
    for row_idx in tqdm(range(2, xl_sheet.nrows), desc='Converting XLSX rows to JSON entries'):
        entry = {} 
        for (field, col_idx) in zip(cols, range(len(cols))):
            value = xlsx_cell_to_json(field, xl_sheet.cell(row_idx, col_idx))
            if value is not None:
                entry[field] = value
        entries.append(entry)
        
    # Emit the file mapping each zip code to all properties in that zip code.
    open(file_json, 'w').write(json.dumps(entries, indent=2, sort_keys=True))

def buses_locations_move_onto_grid(grid, file_json):
    '''
    Move all bus locations onto the grid.
    '''
    buses = json.load(open(file_json, 'r'))
    for bus in tqdm(buses, desc='Moving bus locations onto grid'):
        (lon, lat) = grid.intersection_nearest((bus['Bus Longitude'], bus['Bus Latitude']))
        bus['Bus Longitude'] = lon
        bus['Bus Latitude'] = lat
    open(file_json, 'w').write(json.dumps(buses, indent=2, sort_keys=True))

if __name__ == "__main__":
    grid = Grid('input/segments-prepared.geojson')
    xlsx_to_json('input/bps-buses.xlsx', 'output/buses.json')
    buses_locations_move_onto_grid(grid, 'output/buses.json')

## eof