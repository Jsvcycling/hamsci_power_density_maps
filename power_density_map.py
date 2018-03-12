#!/usr/bin/env python3

import datetime
import glob
import math
import os

import matplotlib as mpl
mpl.use('Agg')

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

INPUT_DIR  = os.path.join('/', 'home', 'vega', 'Documents',
                          'hamsci_conf_2017_out', 'traces')
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

# Get the obscuration for a single point.
def get_obsc(ut_time, lat, lon, alt):
    query = ('''SELECT value FROM midpnt_obsc WHERE
    latitude=%s AND longitude=%s AND time=%s AND altitude=%s
    LIMIT 1''')

    ut_time = ut_time.to_pydatetime()
    lat     = float(lat)
    lon     = float(lon)
    alt     = float(alt)

    cursor.execute(query, (lat, lon, ut_time, alt))
    row = cursor.fetchone()

    if row == None:
        obsc = calc_obsc(ut_time, lat, lon, alt * 1000)

        obsc = float(obsc)

        if math.isnan(obsc):
            print('Found NaN')
            return obsc

        insert = ('''INSERT INTO midpnt_obsc (latitude, longitude,
        time, altitude, value) VALUES (%s, %s, %s, %s, %s)''')

        cursor.execute(insert, (lat, lon, ut_time, alt, obsc))
        db.commit()

        return obsc
    else:
        return row[0]

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

        return obsc
    else:
        return row[0]

# Check if a point is over land.
def is_over_land(lat, lon):
    for land in lands:
        if land.contains(sgeom.Point(lat, lon)): return True

    # If it wasn't found, return False.
    return False

# Load in all trace files into a pandas DataFrame.
def load_traces(input_dir, verbose=False):
    models = { 'base': os.path.join(input_dir, 'base'),
               'eclipse': os.path.join(input_dir, 'eclipse') }

    df = pd.DataFrame()

    for name, folder in models.items():
        print('Loading {} traces:'.format(name))
        
        # Get all the CSV files from the selected directory.
        files = glob.glob(os.path.join(folder, 'simulated_*.csv'))

        for idx, f in enumerate(files):
            if verbose:
                print('    {}'.format(f))

            if name == 'eclipse':
                timestamp = datetime.datetime.strptime(
                    f[-23:-4],
                    '%Y-%m-%d %H:%M:%S'
                )
            elif name == 'base':
                timestamp = datetime.datetime.strptime(
                    f[-23:-4],
                    '%Y-%m-%d %H:%M:%S'
                )
            else:
                raise Exception('Whoops...')
            
            df_tmp = pd.read_csv(f, header=0, index_col=False)

            df_tmp['timestamp'] = timestamp
            df_tmp['ionosphere'] = name

            df_tmp = df_tmp.drop([
                'srch_rd_phase_path',
                'srch_rd_plasma_freq_at_apogee',
                'srch_rd_virtual_height',
                'srch_rd_effective_range',
                'srch_rd_deviative_absorption',
                'srch_rd_TEC_path',
                'srch_rd_Doppler_shift',
                'srch_rd_Doppler_spread',
                'srch_rd_frequency',
                'srch_rd_FAI_backscatter_loss'], axis=1)

            df = df.append(df_tmp, ignore_index=True)
            
        print('Done.')

    df = df.dropna(subset=['srch_rd_apogee_lat',
                           'srch_rd_apogee_lon',
                           'srch_rd_apogee'])
    
    return df

def process_traces(df):
    for idx, row in df.iterrows():
        apogee_obsc = get_obsc(row.timestamp, row.srch_rd_apogee_lat,
                               row.srch_rd_apogee_lon, row.srch_rd_apogee)

        df.set_value(idx, 'apogee_obsc', apogee_obsc)

    df = df.dropna(subset=['apogee_obsc'])

    return df

def main():
    df = load_traces(INPUT_DIR, True)

    print(df.size)
    
    print('Computing midpoint obscurations...', end='', flush=True)
    df = process_traces(df)
    print('Done.')

    print(df.size)
    exit()

    #TODO: Create a matplotlib figure.

    f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 20), dpi=200)
    
    axes = [ax1, ax2, ax3, ax4]

    print('Plotting results...', end='', flush=True)
    # TODO: Plot results
    
    f.savefig(os.path.join(OUTPUT_DIR, 'power_density_map.png'))
    print('Done.')

if __name__ == '__main__':
    main()
