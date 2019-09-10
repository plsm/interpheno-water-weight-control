#!/usr/bin/python
"""
Setups the environment for the plant weight water control system.

There is folder where sound files, data and configuration files are placed.
Sound files are created using the speech synthesiser `flite`.
"""

import argparse
import dropbox
import os
import subprocess
import yaml

import water_plant


def main ():
    args = process_arguments ()
    if not os.path.exists (water_plant.DATA_FOLDER):
        os.makedirs (water_plant.DATA_FOLDER)
    cfg = {
        'token': args.token,
    }
    with open (water_plant.CONFIG_FILENAME, 'wt') as fd:
        yaml.safe_dump (cfg, fd)
    create_sound_file ('Welcome to the plant weight water control system.', 'welcome-message.riff')
    create_sound_file ('Uploaded file with plant weight and watering.', 'upload-watering.riff')
    create_sound_file ('Attention! Could not upload file with plant weight and watering.', 'no-uploading-watering.riff')
    create_sound_file ('Attention! Could not download pump data file.', 'no-download-pump-data.riff')
    create_sound_file ('Downloaded file with experiment data', 'download-experiment-data.riff')
    create_sound_file ('Attention! Could not download experiment data file.', 'no-download-experiment-data.riff')
    create_sound_file ('Attention! Error parsing experiment data file.', 'error-parsing-experiment-data.riff')
    create_sound_file ('Connect barcode scanner.', 'connect-barcode-scanner.riff')
    create_sound_file ('Connect water pump.', 'connect-water-pump.riff')
    create_sound_file ('Connect plant scale.', 'connect-plant-scale.riff')
    create_sound_file ('Waiting for plant barcode...', 'waiting-barcode.riff')
    create_sound_file ('Waiting for plant weight...', 'waiting-weight.riff')
    try:
        dbx = dropbox.Dropbox (args.token)
        dbx.files_download_to_file (water_plant.EXPERIMENT_DATA_FILENAME, '/experiment-data.csv')
    except BaseException as ex:
        print (ex)
    if os.path.exists (water_plant.WATERING_FILENAME):
        answer = input ('Overwrite file {} (y/n)? '.format (water_plant.WATERING_FILENAME))
        ok = answer == 'y' or answer == 'yes'
    else:
        ok = True
    if ok:
        with open (water_plant.WATERING_FILENAME, 'wt') as fd:
            fd.write ('"timestamp","plant id","plant current weight","plant desired weight","watered","motor speed","revolutions","water per 1 revolution"\n')


def create_sound_file (text, filename):
    command = [
        '/usr/bin/flite',
        '-voice', 'slt',
        '-t', text,
        os.path.join (water_plant.DATA_FOLDER, filename)
    ]
    process = subprocess.Popen (
        command
    )
    process.wait ()
    return None


def process_arguments ():
    parser = argparse.ArgumentParser ()
    parser.add_argument (
        '-t',
        '--token',
        type=str,
        required=True,
        help='Dropbox token used to download plant barcodes and upload plant weight readings',
        metavar='N'
        )
    return parser.parse_args ()


if __name__ == '__main__':
    main ()
