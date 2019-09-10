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
EXPERIMENT_DATA_FILENAME = DATA_FOLDER + '/experiment-data.csv'
CONFIG_FILENAME = DATA_FOLDER + '/config.txt'
WATERING_FILENAME = DATA_FOLDER + '/watering.csv'
PUMP_DATA_FILENAME = DATA_FOLDER + '/pump-data.txt'

MOTOR_SPEED = 70

WATER_PER_1_REVOLUTION = 0.849392857142857
WATER_PER_1_REVOLUTION = 0.859535714285714
WATER_PER_1_REVOLUTION = 0.87
WATER_PER_1_REVOLUTION = 0.86
WATER_PER_1_REVOLUTION = 0.85


class Plant:
    def __init__ (self, csv_row):
        self.id = csv_row ['id']
        self.weight = float (csv_row ['weight'])
        self.description = csv_row ['description']


def main ():
    time.sleep (10)
    play_sound ('welcome-message.riff')
    cfg = read_config ()
    download_pump_data_file (cfg ['token'])
    download_experiment_data_file (cfg ['token'])
    upload_watering (cfg ['token'])
    dict_plants = read_experiment_data_file ()
    barcode = detect_barcode_scanner ()
    pump = detect_pump ()
    try:
        scale = detect_scale ()
        while True:
            plant_id = get_plant_code_reading (barcode)
            if report_plant_code (plant_id, dict_plants):
                plant_weight = get_scale_reading (scale)
                water_plant (plant_id, plant_weight, dict_plants [plant_id].weight, pump)
    except BaseException as ex:
        write_to_log ('erro [{}]'.format (ex))
        raise ex
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


def download_pump_data_file (token):
    global MOTOR_SPEED
    global WATER_PER_1_REVOLUTION
    try:
        dbx = dropbox.Dropbox (token)
        write_to_log ('connected to dropbox account')
        dbx.files_download_to_file (PUMP_DATA_FILENAME, '/pump-data.txt')
        write_to_log ('downloaded pump data file')
        with open (PUMP_DATA_FILENAME, 'r') as fd:
            exp = yaml.safe_load (fd)
        if exp ['motor_speed'] != MOTOR_SPEED or\
                exp ['water_per_1_revolution'] != WATER_PER_1_REVOLUTION:
            write_to_log ('new pump data parameters ')
            MOTOR_SPEED = exp ['motor_speed']
            WATER_PER_1_REVOLUTION = exp = exp ['water_per_1_revolution']
            synthesise_text ('Set the water pump parameters. The motor speed is {}. The water weight per one revolution is {} grams'.format (
                MOTOR_SPEED,
                WATER_PER_1_REVOLUTION
            ))
        result = True
    except BaseException as ex:
        write_to_log ('an error occur while downloading pump data file {}'.format (ex))
        play_sound ('no-download-pump-data.riff')
        result = False
    return result


def detect_barcode_scanner ():
    """Wait for the barcode scanner to be connected to the raspberry pi.

    Per the `dmesg` command, the barcode scanner is assigned the device filename

        /dev/input/by-id/usb-SHANG_CHEN_DIAN_ZI_SHANG_CHEN_HID_SC-32-event-kbd

    We don't check for this file, instead we check for '/dev/hidraw0' which
    is the only input device that will be connected to the raspberry pi.
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
    # noinspection SpellCheckingInspection
    device = '/dev/ttyUSB0'
    while not os.path.exists (device):
        write_to_log ('waiting for pump to be connected...')
        play_sound ('connect-water-pump.riff')
        time.sleep (10)
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
        play_sound ('connect-plant-scale.riff')
        time.sleep (10)
    result = serial.Serial (device, 9600, timeout=0)
    write_to_log ('detected scale at device [{}]'.format (device))
    return result


def download_experiment_data_file (token):
    """
    Download the plant data file from the dropbox folder associated with the given token.
    The file is saved in the location given by variable `EXPERIMENT_DATA_FILENAME`.
    :param: token: the dropbox token.
    """
    try:
        dbx = dropbox.Dropbox (token)
        write_to_log ('connected to dropbox account')
        dbx.files_download_to_file (EXPERIMENT_DATA_FILENAME, '/experiment-data.csv')
        write_to_log ('downloaded experiment data file')
        play_sound ('download-experiment-data.riff')
        result = True
    except BaseException as ex:
        write_to_log ('an error occur while downloading experiment data file {}'.format (ex))
        play_sound ('no-download-experiment-data.riff')
        result = False
    return result


def read_experiment_data_file ():
    """
    Read the experiment data file containing information about wich plants should be watered
    and return a dictionary with id's associated with plant data.
    """
    try:
        with open (EXPERIMENT_DATA_FILENAME, 'r') as fd:
            reader = csv.DictReader (
                fd,
                quoting=csv.QUOTE_NONNUMERIC,
                delimiter=',',
            )
            result = {
                row ['id']: Plant (row)
                for row in reader
            }
    except BaseException:
        try:
            with open (EXPERIMENT_DATA_FILENAME, 'r') as fd:
                reader = csv.DictReader (
                    fd,
                    quoting=csv.QUOTE_NONNUMERIC,
                    delimiter=';',
                )
                result = {
                    row ['id']: Plant (row)
                    for row in reader
                }
        except BaseException:
            try:
                with open (EXPERIMENT_DATA_FILENAME, 'r') as fd:
                    reader = csv.DictReader (
                        fd,
                        delimiter=';',
                    )
                    result = {
                        row ['id']: Plant (row)
                        for row in reader
                    }
            except BaseException:
                play_sound ('error-parsing-experiment-data.riff')
    print (result)
    return result


hid = {
    4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i', 13: 'j', 14: 'k', 15: 'l', 16: 'm',
    17: 'n', 18: 'o', 19: 'p', 20: 'q', 21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x', 28: 'y', 29: 'z',
    30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7', 37: '8', 38: '9', 39: '0', 44: ' ', 45: '-', 46: '=',
    47: '[', 48: ']', 49: '\\', 51: ';', 52: '\'', 53: '~', 54: ',', 55: '.', 56: '/'
}

hid2 = {
    4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K', 15: 'L', 16: 'M',
    17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V', 26: 'W', 27: 'X', 28: 'Y', 29: 'Z',
    30: '!', 31: '@', 32: '#', 33: '$', 34: '%', 35: '^', 36: '&', 37: '*', 38: '(', 39: ')', 44: ' ', 45: '_', 46: '+',
    47: '{', 48: '}', 49: '|', 51: ':', 52: '"', 53: '~', 54: '<', 55: '>', 56: '?'
}


def get_plant_code_reading (barcode_scanner_device):
    """
    Get a plant code using the barcode scanner.

    The code of this function was taken from `https://github.com/rgrokett/TalkingBarcodeReader`.
    :return: a long number.
    """
    play_sound ('waiting-barcode.riff')
    fd = open (barcode_scanner_device, 'rb')
    ss = ''
    shift = False
    done = False
    while not done:
        # Get the character from the HID
        buffer = fd.read (8)
        for c in buffer:
            if ord (c) > 0:
                # 40 is carriage return which signifies
                # we are done looking for characters
                if int (ord (c)) == 40:
                    done = True
                    break
                # If we are shifted then we have to
                # use the hid2 characters.
                if shift:
                    # If it is a '2' then it is the shift key
                    if int (ord (c)) == 2:
                        shift = True
                    # if not a 2 then lookup the mapping
                    else:
                        ss += hid2[int (ord (c))]
                        shift = False
                # If we are not shifted then use
                # the hid characters
                else:
                    # If it is a '2' then it is the shift key
                    if int (ord (c)) == 2:
                        shift = True
                    # if not a 2 then lookup the mapping
                    else:
                        ss += hid[int (ord (c))]
    fd.close ()
    result = ss
    write_to_log ('read plant code {}'.format (result))
    return result


def report_plant_code (code, plants):
    """
    Say to the user the plant code and description.

    If the code does not exist, we report this incident.
    :param code: the plant code read by the barcode scanner.
    :param plants: the plant dictionary.
    :return: `True` if the code exists in the dictionary.
    """
    ok = code in plants
    if ok:
        synthesise_text ('Read plant code {}. The description is {}.'.format (
            ' '.join (str (code)),
            plants [code].description,
        ))
    else:
        write_to_log ('non existing plant code {}'.format (
            code
        ))
        synthesise_text ('Warning! Unknown plant code {}.'.format (
            ' '.join (str (code)),
        ))
    return ok


def get_scale_reading (scale):
    """
    Get a scale reading.
    """
    write_to_log ('waiting for scale to return a reading')
    play_sound ('waiting-weight.riff')
    ko = True
    while ko:
        reading = scale.readline ()
        if len (reading) == 0:
            play_sound ('waiting-weight.riff')
            time.sleep (10)
        else:
            ko = False
    write_to_log ('scale returned the reading [{}]'.format (reading))
    weight = reading [1:9]
    try:
        result = float (weight)
    except ValueError:
        result = get_scale_reading (scale)
    return result


def water_plant (plant_id, plant_current_weight, plant_desired_weight, pump):
    delta_weight = plant_desired_weight - plant_current_weight
    if delta_weight > 0:
        write_to_log ('plant id {} needs {}g of water'.format (plant_id, delta_weight))
        revolutions = '{:.2f}'.format (delta_weight / WATER_PER_1_REVOLUTION)
        pump.setMotorSpeed (MOTOR_SPEED)
        pump.setRevolutions (revolutions)
        pump.go ()
        write_to_log ('set the pump speed to {} and pump revolutions to {}'.format (MOTOR_SPEED, revolutions))
        record_watering (plant_id, plant_current_weight, plant_desired_weight, MOTOR_SPEED, revolutions)
    else:
        write_to_log ('plant id {} has excess water, {}g'.format (plant_id, -delta_weight))
        record_weight (plant_id, plant_current_weight, plant_desired_weight)
    return None


def record_watering (plant_id, plant_current_weight, plant_desired_weight, motor_speed, revolutions):
    """
    Record a watering event.
    """
    now = datetime.datetime.now ()
    with open (WATERING_FILENAME, 'at') as fd:
        fd.write ('"{}",{},{},{},1,{},{},{}\n'.format (
            now.isoformat (),
            plant_id,
            plant_current_weight,
            plant_desired_weight,
            motor_speed,
            revolutions,
            WATER_PER_1_REVOLUTION
            )
        )


def record_weight (plant_id, plant_current_weight, plant_desired_weight):
    """Record a plant weight.

    Used when there is no watering.
    """
    now = datetime.datetime.now ()
    with open (WATERING_FILENAME, 'at') as fd:
        fd.write ('"{}",{},{},{},0,,,\n'.format (
            now.isoformat (),
            plant_id,
            plant_current_weight,
            plant_desired_weight
            )
        )


def upload_watering (token):
    try:
        dbx = dropbox.Dropbox (token)
        write_to_log ('connected to dropbox account')
        # read the content
        with open (WATERING_FILENAME, 'r') as fd:
            content = ''
            for line in fd:
                content += line
            content = bytes (content)
        dbx.files_upload (
            content,
            '/watering.csv',
            mode=dropbox.files.WriteMode.overwrite,
        )
        write_to_log ('uploaded watering file')
        play_sound ('upload-watering.riff')
        result = True
    except BaseException as ex:
        write_to_log ('an error occur while uploading watering file {}'.format (ex))
        play_sound ('no-uploading-watering.riff')
        result = False
    return result


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
    seconds and checks the existence of the file every `check_time`
    seconds.

    :param filename: the device filename to wait for.
    :param timeout: how many seconds to wait for.
    :param check_time: the filename existence period (in seconds).

    :return: `True` if the device filename exists.
    """
    elapsed = 0
    while not os.path.exists (filename) and elapsed < timeout:
        time.sleep (check_time)
        elapsed += check_time
    return os.path.exists (filename)


def write_to_log (message):
    print (message)
    with open ('/var/log/interpheno/controlo-peso-planta.log', 'at') as fd:
        fd.write ('{}: {}\n'.format (
            datetime.datetime.now ().isoformat (),
            message
            ))
    return None


if __name__ == '__main__':
    main ()
