#!/usr/bin/env python3

import cartopy.io.shapereader as shapereader
import matplotlib.pyplot as plt
import mysql.connector as mysql
import numpy as np
import pandas as pd
import shapely.geometry as sgeom

# TODO: we need to import the eclipse calculator stuff.

# Use population density to mask out oceans, etc.
USE_POPDENSITY = True

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
    `id` INT NOT NULL AUTO_INCREMENT,
    `latitude` FLOAT NOT NULL,
    `longitude` FLOAT NOT NULL,
    `altitude` FLOAT NOT NULL,
    `value` FLOAT NOT NULL
    )''')
except Exception as e:
    print(e)

# Lookup the midpoint obscuration of the midpoint. If it doesn't exist in the
# database, calculate it and insert it into the database.
def get_midpoint_obscuration(lat, lon, alt):
    pass

# Check if a point is over land.
def is_over_land(lat, lon):
    for land in lands:
        if land.contains(sgeom.Point(lat, lon)): return True

    # If it wasn't found, return False.
    return False
