#!/usr/bin/python

from __future__ import print_function

import csv
import os
import sys
import serial
import time
import dropbox

#import masterflex


def detect_pump ():
    """
    Search for the serial connection where the pump is connected to.
    :return: an instance of Masterflex
    """
    device = '/dev/ttyUSB0'
    result = masterflex.MasterflexSerial (1, device)
    write_to_log ('detected pump at device [{}]'.format (device))
    return result


def detect_scale ():
    """
    Get a serial connection to the scale.
    :return: an instance of Serial.
    """
    device = '/dev/ttyUSB1'
    result = serial.Serial (device, 9600, timeout=0)
    write_to_log ('detected scale at device [{}]'.format (device))
    return result


def download_plant_weight_file (token):
    try:
        dbx = dropbox.Dropbox (token)
        write_to_log ('connected to dropbox account')
        dbx.files_download_to ('/home/pi/water-weight-control/peso-plantas.csv', 'peso-plantas.csv')
        write_to_log ('downloaded plant weight file')
        result = True
    except BaseException as ex:
        write_to_log ('an error occur while downloading plant weight file '.format (ex))
        result = False
    return result


def read_ideal_plant_weight_file (token):
    dbx = dropbox.Dropbox (token)
    for entry in dbx.files_list_folder('').entries:
        print (entry.name)
    return None


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
    Get a scale reading 
    """
    reading = scale.readline ()
    write_to_log ('scale returned the reading [{}]'.format (reading))
    weight = reading [1:9]
    result = float (weight)
    return result

def write_to_log (message):
    with open ('/var/log/interpheno/controlo-peso-planta.log', 'at') as fd:
        fd.write ('{}: {}'.format (
            datetime.now ().isoformat (),
            message
            ))
    return None

