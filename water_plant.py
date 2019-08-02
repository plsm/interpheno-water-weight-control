#!/usr/bin/python

from __future__ import print_function

import csv
import datetime
import dropbox
import os
import os.path
import sys
import serial
import time
import yaml

#import masterflex

PLANT_WEIGHT_FILENAME = '/home/pi/water-weight-control/peso-plantas.csv'
CONFIG_FILENAME = '/home/pi/water-weight-control/config.txt'


def main ():
    cfg = read_config ()
    pump = detect_pump ()
    scale = detect_scale ()


def read_config ():
    """
    Read the configuration file and return a dictionary.
    """
    with open (CONFIG_FILENAME, 'r') as fd:
        result = yaml.safe_load (fd)
    write_to_log ('read configuration file')
    return result


def detect_pump ():
    """
    Search for the serial connection where the pump is connected to.
    :return: an instance of Masterflex
    """
    device = '/dev/ttyUSB0'
    while not os.path.exists (device):
        write_to_log ('waiting for pump to be connected...')
        time.sleep (30)
    result = masterflex.MasterflexSerial (1, device)
    write_to_log ('detected pump at device [{}]'.format (device))
    return result


def detect_scale ():
    """
    Get a serial connection to the scale.
    :return: an instance of Serial.
    """
    device = '/dev/ttyUSB1'
    while not os.path.exists (device):
        write_to_log ('waiting for scale to be connected...')
        time.sleep (30)
    result = serial.Serial (device, 9600, timeout=0)
    write_to_log ('detected scale at device [{}]'.format (device))
    return result


def download_plant_weight_file (token):
    """
    Download the plant weight file from the dropbox folder associated with the given token.
    The file is saved in the location given by variable `PLANT_WEIGHT_FILENAME`.
    :param: token: the dropbox token.
    """
    try:
        dbx = dropbox.Dropbox (token)
        write_to_log ('connected to dropbox account')
        dbx.files_download_to_file (PLANT_WEIGHT_FILENAME, '/peso-plantas.csv')
        write_to_log ('downloaded plant weight file')
        result = True
    except BaseException as ex:
        write_to_log ('an error occur while downloading plant weight file {}'.format (ex))
        result = False
    return result


def read_plant_weight_file ():
    """
    Read the plant weight file and return a dictionary with id's associated with weights.
    """
    with open (PLANT_WEIGHT_FILENAME, 'r') as fd:
        reader = csv.DictReader (
            fd,
            quoting=csv.QUOTE_NONNUMERIC,
            delimiter=',',
        )
        result = {
            int (row ['id']) : row ['weight']
            for row in reader
            }
    return result


def get_plant_code_reading ():
    """
    Get a plant code using the bar code.
    :return: a long number.
    """
    try:
        result = int (input ())
        write_to_log ('read plant code {}'.format (resultado))
        return result
    except BaseException as ex:
        write_to_log ('an error occurred while reading plant code: {}'.format (ex))
        time.sleep (60)
        return get_bar_code_reading ()
    

def get_scale_reading (scale):
    """
    Get a scale reading.
    """
    reading = scale.readline ()
    write_to_log ('scale returned the reading [{}]'.format (reading))
    weight = reading [1:9]
    result = float (weight)
    return result


def write_to_log (message):
    print (message)
    with open ('/var/log/interpheno/controlo-peso-planta.log', 'at') as fd:
        fd.write ('{}: {}\n'.format (
            datetime.datetime.now ().isoformat (),
            message
            ))
    return None

