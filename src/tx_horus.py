#!/usr/bin/env python
#
#	Raspberry Pi Horus Binary v2 Transmitter Script. Transmits position from GPS input.
#
#	Copyright (C) 2024  Andrew Koenig <ke5gdb@gmail.com>
#						Mark Jessop <vk5qi@rfhead.net>
#	Released under GNU GPL v3 or later
#

import argparse
import logging
import time
import os
import datetime
import subprocess
import traceback
import codecs

import horusdemodlib.encoder
import PacketTX
import ublox

parser = argparse.ArgumentParser()
parser.add_argument("id", type=int, default=256, help="Payload Horus v2 ID. Defaults to 256 / 4FSKTEST-V2")
parser.add_argument("--gps", default="none", help="uBlox GPS Serial port. Defaults to /dev/ttyACM0")
parser.add_argument("--frequency", default=434.200, type=float, help="Transmit Frequency (MHz). (Default: 434.200 MHz)")
parser.add_argument("--autorestart", default=20, type=int, help="Number of packets to transmit continuously before restarting TX process. (Default: 20)")
parser.add_argument("-v", "--verbose", action='store_true', default=False, help="Show additional debug info.")
args = parser.parse_args()

if args.verbose:
	logging_level = logging.DEBUG
else:
	logging_level = logging.INFO

# Set up logging
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging_level)

id = args.id
if id < 256 or id > 65535:
	logging.critical("Invalid Horus v2 ID specified! Exiting")
	sys.exit(1)

print("Using payload ID: %s" % id)

tx = PacketTX.PacketTX(frequency=args.frequency, autorestart=args.autorestart, log_file="debug.log")
tx.start_tx()

# Initialize global variables
system_time_set = False
max_altitude = -1
sequence = 0
gps_data = None

# Disable Systemctl NTP synchronization so that we can set the system time on first GPS lock.
# This is necessary as NTP will refuse to sync the system time to the information we feed it via ntpshm unless
# the system clock is already within a few seconds.
if args.gps.lower() != 'none':
	ret_code = os.system("timedatectl set-ntp 0")
	if ret_code == 0:
		logging.debug("GPS Debug: Disabled NTP Sync until GPS lock.")
	else:
		logging.debug("GPS Debug: Could not disable NTP sync.")

def handle_gps_data(gps_data_in):
	""" Handle GPS data passed to us from the UBloxGPS instance """
	global max_altitude, tx, system_time_set, gps_data

	gps_data = gps_data_in

	# If we have GPS fix, update the max altitude field.
	if (gps_data['altitude'] > max_altitude) and (gps_data['gpsFix'] == 3):
		max_altitude = gps_data['altitude']

	# If we have GPS lock, set the system clock to it. (Only do this once.)
	if (gps_data['gpsFix'] == 3) and not system_time_set:
		dt = gps_data['datetime']
		try:
			new_time = dt.strftime('%Y-%m-%d %H:%M:%S')
			ret_code = os.system("timedatectl set-time \"%s\"" % new_time)
			if ret_code == 0:
				logging.debug("GPS Debug: System clock set to GPS time %s" % new_time)
			else:
				logging.debug("GPS Debug: Attempt to set system clock failed!")
			system_time_set = True

			# Re-enable NTP synchronisation
			ret_code = os.system("timedatectl set-ntp 1")
			if ret_code == 0:
				logging.debug("GPS Debug: Re-enabled NTP sync.")
			else:
				logging.debug("GPS Debug: Could not enable NTP sync.")
		except:
			logging.debug("GPS Debug: Attempt to set system clock failed!")

	if gps_data['gpsFix'] != 3:
		gps_data = None


# Try and start up the GPS rx thread.

try:
	if args.gps.lower() != 'none':
		gps = ublox.UBloxGPS(port=args.gps,
			dynamic_model = ublox.DYNAMIC_MODEL_AIRBORNE1G,
			update_rate_ms = 1000,
			debug_ptr = logging.debug,
			callback = handle_gps_data,
			log_file = 'gps_data.log'
			)
	else:
		logging.critical("No GPS configured. Exiting")
		sys.exit(1)
except Exception as e:
	logging.critical("ERROR: Could not Open GPS - %s" % str(e))
	sys.exit(1)

encoder = horusdemodlib.encoder.Encoder()

# Main 'loop'.
try:
	while True:
		# Create Horus Binary Packet, send to tx thread
		if not tx.staged_packet and gps_data:
			packet = encoder.create_horus_v2_packet(
				return_uncoded=False,
				payload_id=id,
				sequence_number=sequence,
				latitude=gps_data['latitude'],
				longitude=gps_data['longitude'],
				altitude=gps_data['altitude'],
				speed=gps_data['ground_speed'],
				satellites=gps_data['numSV'],
				time_dt=datetime.datetime.utcnow()
			)

			tx.stage_packet(codecs.encode(packet, 'hex').decode().upper())
			sequence += 1

		time.sleep(.1)

# Catch CTRL-C, and exit cleanly.
# Only really used during debugging.
except KeyboardInterrupt:
	print("Closing")
	gps.close()
	tx.close()
