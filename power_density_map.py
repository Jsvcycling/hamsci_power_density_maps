#!/usr/bin/env python3

import os

import cartopy.io.shapereader as shapereader
import matplotlib.pyplot as plt
import mysql.connector as mysql
import numpy as np
import pandas as pd
import shapely.geometry as sgeom

# Import the obscuration calculator
from eclipse_calculator.eclipse_calc import calculate_obscuration as calc_obsc

# Import geographiclib (for midpoint calculator)
from geographiclib.geodesic import Geodesic

# MySQL credentials
MYSQL_USERNAME = 'hamsci'
MYSQL_PASSWORD = 'hamsci'
MYSQL_HOST     = 'localhost'
MYSQL_DATABASE = 'pwr_density_map_data'

MAP_RES  = '110m'
MAP_TYPE = 'physical'
MAP_NAME = 'land'

INPUT_DIR  = 'input'
OUTPUT_DIR = 'output'

shape_data = shapereader.natural_earth(resolution=MAP_RES, category=MAP_TYPE,
                                       name=MAP_NAME)
lands = shapereader.Reader(shape_data).geometries()

# Connect to the database
db = mysql.connect(user=MYSQL_USERNAME, password=MYSQL_PASSWORD,
                   host=MYSQL_HOST, database=MYSQL_DATABASE)

# Create a DB cursor
cursor = db.cursor()

try:
    cursor.execute('''CREATE TABLE IF NOT EXISTS midpnt_obsc (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `latitude` FLOAT NOT NULL,
    `longitude` FLOAT NOT NULL,
    `time` DATETIME NOT NULL,
    `altitude` FLOAT NOT NULL,
    `value` FLOAT NOT NULL,
    KEY(latitude, longitude, time, altitude)
    )''')
except Exception as e:
    print(e)
    exit()

# Lookup the midpoint obscuration of the midpoint. If it doesn't exist in the
# database, calculate it and insert it into the database.
def get_midpoint_obscuration(ut_time, lat1, lon1, lat2, lon2, alt):
    line = Geodesic.WGS84.InverseLine(lat1, lon1, lat2, lon2)
    mid  = line.Position(0.5 * line.s13)
    
    query = ('''SELECT value FROM midpnt_obsc WHERE
    latitude=%s AND longitude=%s AND time=%s AND altitude=%s
    LIMIT 1''')

    cursor.execute(query, (mid[0], mid[1], ut_time, alt))
    row = cursor.fetchone()

    if row == None:
        obsc = calc_obsc(ut_time, mid[0], mid[1], alt * 1000)

        insert = ('''INSERT INTO midpnt_obsc (latitude, longitude,
        time, altitude, value) VALUES (%s, %s, %s, %s, %s)''')

        cursor.execute(insert, (mid[0], mid[1], ut_time, alt, obsc))
    else:
        return row[0]

# Check if a point is over land.
def is_over_land(lat, lon):
    for land in lands:
        if land.contains(sgeom.Point(lat, lon)): return True

    # If it wasn't found, return False.
    return False

def main():
    print('Loading input...', end='', flush=True)
    # TODO: Load in every trace file.
    print('Done.')
    
    print('Computing midpoint obscurations...', end='', flush=True)
    # TODO: Compute midpoint obscuration for each (split it up and use
    # multhithreading to speed up).
    print('Done.')

    #TODO: Create a matplotlib figure.

    print('Plotting results...', end='', flush=True)
    # TODO: Plot the output and save.
    print('Done.')

if __name__ == '__main__':
    main()
