"""
generate-bus-data.py

Module for automatically generating a simulated bus data set.
"""

import os
import json
import xlrd
from tqdm import tqdm

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
    """
    Converts a bus data XLSX spreadsheet into a JSON file.
    """
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

def main():
    xlsx_to_json('input/bps-buses.xlsx', 'output/buses.json')

main()

## eof