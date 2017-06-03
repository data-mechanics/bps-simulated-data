# Simulated Student Data for Boston Public Schools
Tool for automatically generating simulated data sets of Boston Public Schools students, their school assignments, their bus stop assignments, and bus routes.

## Usage

To install all requirements:

    python -m pip install --upgrade --no-cache-dir -r requirements.txt

To execute the script and generate individual data sets (placed in the `output` subdirectory by default):

    python generate-student-data.py
    python generate-bus-data.py
    python generate-stop-data.py

To generate a compiled Excel workbook (appropriate for submission to the [bps-challenge-score scoring tool](https://github.com/Data-Mechanics/bps-challenge-score):

    python generate-compiled-data.py

## Example Output

Once the data has been generated, load `visualization.html` in any browser to view a rendering that uses the [Leaflet](http://leafletjs.com/) library.

![Visualization of generated data using Leaflet](visualization.png)

## Data Sources

* [Public Schools](https://data.boston.gov/dataset/public-schools) at `data.boston.gov`
* [Boston Census Blocks](http://worldmap.harvard.edu/data/geonode:c_bra_bl) at `worldmap.harvard.edu`
* [Property Assessment 2014](https://data.cityofboston.gov/dataset/Property-Assessment-2014/qz7u-kb7x) from `data.cityofboston.gov`
* [Zip codes](http://www.mass.gov/anf/research-and-tech/it-serv-and-support/application-serv/office-of-geographic-information-massgis/datalayers/zipcodes.html) from `mass.gov`
* [Boston family household data](https://www.bostonplans.org/getattachment/caf0d3fb-951d-4b0a-9181-9b41cdf59cf8) frpm `bostonplans.org`
* [Children per household](https://nces.ed.gov/programs/digest/d15/tables/dt15_102.10.asp?current=yes) from `ed.gov`
