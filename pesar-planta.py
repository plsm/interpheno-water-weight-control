#!/usr/bin/python

from __future__ import print_function

import csv
import os
import sys
import serial
import time


def ler_codigo_planta ():
    """
    O leitor de codigo de barras pode funcionar com um teclado, para ler o codigo usa-se o standard input.
    """
    try:
        resultado = int (input ())
        write_to_log ('read plant code {}'.format (resultado))
        return resultado
    except BaseException as ex:
        write_to_log ('an error occurred while reading plant code: {}'.format (ex))
        time.sleep (60)
        return ler_codigo_planta ()


def obter_peso_ideal_planta (codigo_planta):
    with open ('plantas.csv') as csv_ficheiro:
        reader = csv.DictReader (csv_ficheiro)
        for linha in reader:
            if int (linha ['codigo']) == codigo_planta:
                return linha ['peso']
    return None


def ler_peso_vaso ():
    print ('Test leitura balanca')
    scale = serial.Serial ('/dev/ttyUSB0', 9600, timeout=0)
    reading = scale.readline ()
    write_to_log ('scale returned the reading [{}]'.format (reading))
    weight = reading [1:9]
    result = float (weight)
    scale.close ()
    return result


STX = '\x02'
ENQ = '\x05'
CR = '\x0D'

def controlar_bomba ():
    bomba = serial.Serial (
            '/dev/ttyUSB0',
            4800,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.SEVENBITS,
            #rtscts=True
            )
    # enviar o comando ENQ
    if True:
        comando = ENQ
        bomba.write (bytearray ([bytes (c) for c in comando]))
        bomba.flush ()
        print ('A espera da resposta do comando ')
        print_serial (comando)
        resposta = receive_frame (bomba) # bomba.readline ()
        print ('Resposta e')
        print_serial (resposta)
    if True:
        comando = STX + 'P99I' + CR
        bomba.write (bytearray ([bytes (c) for c in comando]))
        bomba.flush ()
        print ('A espera da resposta do comando ')
        print_serial (comando)
        resposta = receive_frame (bomba)
        print ('Resposta e')
        print_serial (resposta)

    comando = chr (2) + 'P' + '02' + 'R' + chr (13)
    bomba.write (comando)
    bomba.flush ()
    print ('A espera da resposta do comando ')
    print_serial (comando)
    # resposta = bomba.readline ()
    # print_serial (resposta)

    print ('Ligar bomba')
    comando = chr (2) + 'P' + '02' + 'S' + '+0001' + chr (13)
    bomba.write (comando)
    bomba.flush ()

    print ('Desligar bomba')
    input ('Carregue em ENTER')
    comando = chr (2) + 'P' + '01' + 'H' + chr (13)
    bomba.write (comando)
    bomba.flush ()
    serial.close ()
    print ('Fim do controlo da bomba')


def receive_frame (serial):
    raw_data = b''
    raw_byte = serial.read ()
    if raw_byte == STX:
        while raw_byte:
            raw_data += raw_byte
            raw_byte = serial.read ()
    else:
        raw_data += raw_byte
    return raw_data


def print_serial (chars):
    for c in chars:
        print (' {:3}'.format (ord (c)), end='')
    print ()
    for c in chars:
        if ord (c) < 32:
            print ('    ', end='')
        else:
            print ('   {}'.format (c), end='')
    print ()


def write_to_log (message):
    with open ('/var/log/interpheno/controlo-peso-planta.log', 'at') as fd:
        fd.write ('{}: {}'.format (
            datetime.now ().isoformat (),
            message
            )

#ler_codigo_planta ()
#print ('O peso do vaso e {}'.format (ler_peso_vaso ()))

controlar_bomba ()



