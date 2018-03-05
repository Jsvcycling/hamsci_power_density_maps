#!/usr/bin/env python3

import cartopy.io.shapereader as shapereader
import matplotlib.pyplot as plt
import mysql.connector as mysql
import numpy as np
import pandas as pd
import shapely.geometry as sgeom

# Import the obscuration calculator
from eclipse_calc import calculate_obscuration as calc_obsc

# Import geographiclib (for midpoint calculator)
from geographiclib.geodesic import Geodesic

# MySQL credentials
MYSQL_USERNAME = 'hamsci'
MYSQL_PASSWORD = 'hamscience'
MYSQL_HOST     = 'localhost'
MYSQL_DATABASE = 'pwr_density_map_data'

MAP_RES  = '110m'
MAP_TYPE = 'physical'
MAP_NAME = 'land'

shape_data = shapereader.natural_earth(resolution=MAP_RES, category=MAP_TYPE,
                                       name=MAP_NAME)
lands = shapereader.Reader(shape_data).geometries()

# Connect to the database
db = mysql.connector.connect(username=MYSQL_USERNAME, password=MYSQL_PASSWORD,
                             host=MYSQL_HOST, database=MYSQL_DATABASE)

# Create a DB cursor
cursor = db.cursor()

try:
    cursor.execute('''CREATE TABLE IF NOT EXISTS midpnt_obsc (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `latitude` FLOAT NOT NULL KEY,
    `longitude` FLOAT NOT NULL KEY,
    `time` DATETIME NOT NULL KEY,
    `altitude` FLOAT NOT NULL KEY,
    `value` FLOAT NOT NULL
    )''')
except Exception as e:
    print(e)

# Lookup the midpoint obscuration of the midpoint. If it doesn't exist in the
# database, calculate it and insert it into the database.
def get_midpoint_obscuration(ut_time, lat1, lon1, lat2, lon2, alt):
    line = Geodesic.WGS84.InverseLine(lat1, lon1, lat2, lon2)
    mid  = line.Position(0.5 * line.s13)

    # TODO: query the database.
    query = ('''SELECT value FROM midpnt_obsc WHERE
    latitude=%s AND longitude=%s AND time=%s AND altitude=%s
    LIMIT 1''')

    cursor.execute(query, (mid[0], mid[1], ut_time, alt))
    row = cursor.fetchone()

    if row == None:
        return calc_obsc(ut_time, mid[0], mid[1], alt * 1000)
    else:
        return row[0]

# Check if a point is over land.
def is_over_land(lat, lon):
    for land in lands:
        if land.contains(sgeom.Point(lat, lon)): return True

    # If it wasn't found, return False.
    return False

def main():
    print(is_over_land(30, -80))

if __name__ == '__main__':
    main()
