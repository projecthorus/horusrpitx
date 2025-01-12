#!/usr/bin/env python
#
#	Raspberry Pi Horus Binary v2 Transmitter Script. Interfaces to horus4fsk binary. 
#
#	Copyright (C) 2024  Andrew Koenig <ke5gdb@gmail.com>
#						Mark Jessop <vk5qi@rfhead.net>
#	Released under GNU GPL v3 or later
#

import serial
import sys
import os
import datetime
import logging
import shutil
import struct
import subprocess
import traceback
from time import sleep
from threading import Thread
import codecs
import horusdemodlib.encoder

class PacketTX(object):
    def __init__(self,
        frequency = 434.200,
        autorestart=20,
        log_file = None):

        self.frequency = int(frequency * 1e6)
        self.autorestart_count = autorestart

        if log_file != None:
            self.log_file = open(log_file,'a')
            print(f"Opened log file {log_file}")
            self.log_file.write("Started Transmitting at %s\n" % datetime.datetime.utcnow().isoformat())
        else:
            self.log_file = None

        self.staged_packet = None

    def start_tx(self):
        self.transmit_active = True
        txthread = Thread(target=self.tx_thread)
        txthread.start()

    def tx_thread(self):
        while self.transmit_active:
            # Open transmitter process
            cwd = os.getcwd()
            p = subprocess.Popen([os.path.join(cwd, 'mod/horus4fsk'), f'{self.frequency}'],
                                    text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            os.set_blocking(p.stdout.fileno(), False)

            # Iterate through init stdout
            while True:
                sleep(0.1)
                line = p.stdout.readline()
                if line:
                    logging.debug("RPiTX: %s" % line.rstrip())
                else:
                    break

            continuous_tx = True
            packet_count = 0

            while self.transmit_active and continuous_tx:
                if self.staged_packet:
                    logging.debug("Writing packet to stdin: %s" % self.staged_packet)
                    p.stdin.write(f"{self.staged_packet}\n\n")
                    p.stdin.flush()
                    while True:
                        line = p.stdout.readline()
                        if line:
                            logging.debug("RPiTX: %s" % line.rstrip())
                            break
                    self.staged_packet = None
                    packet_count += 1
                    if packet_count == self.autorestart_count:
                        continuous_tx = False
                else:
                    sleep(0.1)

            # Close popen_thread -- send SIGINT
            logging.debug("Closing RPiTX")
            p.terminate()

            sleep(0.5)

    def close(self):
        self.transmit_active = False

    def stage_packet(self, packet):
        logging.debug("Staging packet: %s" % packet)
        self.staged_packet = packet


if __name__ == "__main__":
    """ Test script, which transmits a null packet repeatedly. """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--frequency", default=434.200, type=float, help="Transmit Frequency (MHz). (Default: 434.200 MHz)")
    parser.add_argument("--id", default=256, type=int, help="Payload ID. (Default: 256)")
    parser.add_argument("--lat", default=0, type=float, help="Latitude in Degrees. (Default: 0.0)")
    parser.add_argument("--lon", default=0, type=float, help="Longitude in Degrees. (Default: 0.0)")
    parser.add_argument("--alt", default=0, type=float, help="Altitude in Meters. (Default: 0)")
    parser.add_argument("--sats", default=3, type=int, help="GPS Satellites visible. (Default: 3)")
    parser.add_argument("--autorestart", default=20, type=int, help="Number of packets to transmit continuously before restarting TX process. (Default: 20)")
    parser.add_argument("-v", "--verbose", action='store_true', default=False, help="Show additional debug info.")
    args = parser.parse_args()

    if args.verbose:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    # Set up logging
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging_level)

    e = horusdemodlib.encoder.Encoder()

    tx = PacketTX(
        frequency=args.frequency,
        autorestart=args.autorestart)
    tx.start_tx()

    seq = 0

    try:
        while True:
            # Generate packet
            packet = e.create_horus_v2_packet(
                return_uncoded=False,
                payload_id=args.id,
                sequence_number=seq,
                latitude=args.lat,
                longitude=args.lon,
                altitude=args.alt,
                satellites=args.sats,
                time_dt=datetime.datetime.utcnow()
            )
            tx.stage_packet(codecs.encode(packet, 'hex').decode().upper())
            seq += 1
            sleep(4)

    except KeyboardInterrupt:
        tx.close()
        logging.info("Closing")
