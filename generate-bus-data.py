"""
generate-bus-data.py

Module for automatically generating a simulated bus data set.
"""

import os
import requests
import random
import math
import json
import geojson
import geopy.distance
import shapely.geometry
import xlsxwriter
import rtree
from tqdm import tqdm

def xlsx_to_json(xlsx_file, json_file):
    """
    Converts a bus data spreadsheet into a JSON file.
    """
    pass

def main():
    # Set the random seed to ensure determinism.
    random.seed(1)

    xlsx_to_json('input/bps-buses.xlsx', 'output/buses.json')

main()

## eof