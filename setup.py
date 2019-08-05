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
        'token': args.token
    }
    with open (water_plant.CONFIG_FILENAME, 'wt') as fd:
        yaml.safe_dump (cfg, fd)
    create_sound_file ('Welcome to the plant weight water control system.', 'welcome-message.riff')
    create_sound_file ('Connect barcode scanner.', 'connect-barcode-scanner.riff')
    create_sound_file ('Connect water pump.', 'connect-water-pump.riff')
    create_sound_file ('Connect plant scale.', 'connect-plant-scale.riff')
    try:
        dbx = dropbox.Dropbox (args.token)
        dbx.files_download_to_file (water_plant.PLANT_WEIGHT_FILENAME, '/peso-plantas.csv')
    except BaseException as ex:
        print (ex)


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
