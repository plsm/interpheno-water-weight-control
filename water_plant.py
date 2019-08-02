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

import masterflex

PLANT_WEIGHT_FILENAME = '/home/pi/water-weight-control/peso-plantas.csv'
CONFIG_FILENAME = '/home/pi/water-weight-control/config.txt'


def main ():
    cfg = read_config ()
    pump = detect_pump ()
    scale = detect_scale ()
    download_plant_weight_file (cfg ['token'])
    dicts_id_weight = read_plant_weight_file ()
    while True:
        plant_id = get_plant_code_reading ()
        plant_weight = get_scale_reading (scale)


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


hid = { 4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i', 13: 'j', 14: 'k', 15: 'l', 16: 'm', 17: 'n', 18: 'o', 19: 'p', 20: 'q', 21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x', 28: 'y', 29: 'z', 30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7', 37: '8', 38: '9', 39: '0', 44: ' ', 45: '-', 46: '=', 47: '[', 48: ']', 49: '\\', 51: ';' , 52: '\'', 53: '~', 54: ',', 55: '.', 56: '/'  }

hid2 = { 4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K', 15: 'L', 16: 'M', 17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V', 26: 'W', 27: 'X', 28: 'Y', 29: 'Z', 30: '!', 31: '@', 32: '#', 33: '$', 34: '%', 35: '^', 36: '&', 37: '*', 38: '(', 39: ')', 44: ' ', 45: '_', 46: '+', 47: '{', 48: '}', 49: '|', 51: ':' , 52: '"', 53: '~', 54: '<', 55: '>', 56: '?'  }


def get_plant_code_reading ():
    """
    Get a plant code using the bar code.
    :return: a long number.
    """
    device = '/dev/hidraw2'
    while not os.path.exists (device):
        write_to_log ('waiting for bar code reader to be connected...')
        time.sleep (30)
    write_to_log ('detected bar code reader at device [{}]'.format (device))
    fd = open (device, 'rb')
    ss = ''
    shift = False
    done = False
    while not done:
    # Get the character from the HID
        buffer = fd.read (8)
        for c in buffer:
          if ord (c) > 0:
             ##  40 is carriage return which signifies
             ##  we are done looking for characters
             if int (ord (c)) == 40:
                done = True
                break;
             ##  If we are shifted then we have to
             ##  use the hid2 characters.
             if shift:
                ## If it is a '2' then it is the shift key
                if int (ord (c)) == 2 :
                   shift = True
                ## if not a 2 then lookup the mapping
                else:
                   ss += hid2 [int (ord (c)) ]
                   shift = False
             ##  If we are not shifted then use
             ##  the hid characters
             else:
                ## If it is a '2' then it is the shift key
                if int (ord (c)) == 2 :
                   shift = True
                ## if not a 2 then lookup the mapping
                else:
                   ss += hid [int (ord (c))]
    fd.close ()
    result = int (ss)
    write_to_log ('read plant code {}'.format (result))
    return result


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

