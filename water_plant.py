#!/usr/bin/python

from __future__ import print_function

import csv
import datetime
import dropbox
import os
import os.path
import sys
import serial
import subprocess
import time
import yaml

import masterflex

DATA_FOLDER = '/home/pi/water-weight-control'
PLANT_WEIGHT_FILENAME = DATA_FOLDER + '/peso-plantas.csv'
CONFIG_FILENAME = DATA_FOLDER + '/config.txt'

WATER_PER_1_REVOLUTION = 0.849392857142857


def main ():
    cfg = read_config ()
    pump = detect_pump ()
    try:
        scale = detect_scale ()
        download_plant_weight_file (cfg ['token'])
        dicts_id_weight = read_plant_weight_file ()
        while True:
            plant_id = get_plant_code_reading ()
            plant_weight = get_scale_reading (scale)
            water_plant (plant_id, plant_weight, dicts_id_weight [plant_id], pump)
    finally:
        pump.halt ()
        pump.cancel ()


def read_config ():
    """
    Read the configuration file and return a dictionary.
    """
    with open (CONFIG_FILENAME, 'r') as fd:
        result = yaml.safe_load (fd)
    write_to_log ('read configuration file')
    return result


def detect_barcode_scanner ():
    """Wait for the barcode scanner to be connected to the raspberrypi.

    Per the `dmesg` command, the barcode scanner is assigned the device filename

        /dev/input/by-id/usb-SHANG_CHEN_DIAN_ZI_SHANG_CHEN_HID_SC-32-event-kbd

    We don't check for this file, instead we check for '/dev/hidraw0' which
    is the only input device that will be connected to the raspberrypi.
    """
    device = '/dev/hidraw0'
    while not os.path.exists (device):
        write_to_log ('waiting for bar code reader to be connected...')
        play_sound ('connect-barcode-scanner.riff')
        wait_for_file (device, 10)
    write_to_log ('detected bar code reader at device [{}]'.format (device))
    return device


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


def get_plant_code_reading (barcode_scanner_device):
    """
    Get a plant code using the barcode scanner.

    The code of this function was taken from `https://github.com/rgrokett/TalkingBarcodeReader`.
    :return: a long number.
    """
    fd = open (barcode_scanner_device, 'rb')
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
    synthesise_text ('read plant code {}'.format (' '.join (str (result))))
    return result


def get_scale_reading (scale):
    """
    Get a scale reading.
    """
    ko = True
    while ko:
        reading = scale.readline ()
        if len (reading) == 0:
            write_to_log ('waiting for scale to return a reading')
            time.sleep (10)
        else:
            ko = False
    write_to_log ('scale returned the reading [{}]'.format (reading))
    weight = reading [1:9]
    result = float (weight)
    return result


def water_plant (plant_id, plant_current_weight, plant_desired_weight, pump):
    delta_weight = plant_desired_weight - plant_current_weight
    if delta_weight > 0:
        write_to_log ('plant id {} needs {}g of water'.format (plant_id, delta_weight))
        MOTOR_SPEED = 100
        revolutions = '{:.2}'.format (delta_weight / WATER_PER_1_REVOLUTION)
        pump.setMotorSpeed (MOTOR_SPEED)
        pump.setRevolutions (revolutions)
        pump.go ()
        write_to_log ('set the pump speed to {} and pump revolutions to {}'.format (MOTOR_SPEED, revolutions))
    else:
        write_to_log ('plant id {} has excess water, {}g'.format (plant_id, -delta_weight))
    return None


def play_sound (sound):
    """
    Play the sound in the given filename.

    Sound files are located in the folder `/home/pi/water-weight-control`.

    The function returns after the sound has been played.

    :param sound: the sound filename.
    """
    command = [
        '/usr/bin/omxplayer',
        '--no-osd',
        '--no-keys',
        os.path.join ('/home/pi/water-weight-control', sound)
    ]
    process = subprocess.Popen (
        command
    )
    process.wait ()
    return None


def synthesise_text (text):
    """
    Use the speech synthesizer to play the given text.

    The function returns after the text has been spoken.

    :param text: the text to be spoken.
    """
    command = [
        '/usr/bin/flite',
        '-voice', 'slt',
        '-t', text
    ]
    process = subprocess.Popen (
        command
    )
    process.wait ()
    return None


def wait_for_file (filename, timeout, check_time = 1):
    """Waits for the given filename to appear in the file system.

    This function is used by the application to wait for devices to be
    connected to the raspberry pi.  The function waits at most `timeout`
    seconds and checks the existance of the file every `check_time`
    seconds.

    :param filename: the device filename to wait for.
    :param timeout: how many seconds to wait for.
    :param check_time: the filename existence period (in seconds).

    :return: `True` if the device filename exists.
    """
    ellapsed = 0
    while not os.path.exists (filename) and ellapsed < timeout:
        time.sleep (check_time)
        ellapsed += check_time
    return os.path.exists (filename)


def write_to_log (message):
    print (message)
    with open ('/var/log/interpheno/controlo-peso-planta.log', 'at') as fd:
        fd.write ('{}: {}\n'.format (
            datetime.datetime.now ().isoformat (),
            message
            ))
    return None

