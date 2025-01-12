# Horus Binary Telemetry Transmitter

Transmit Horus Binary v2 using the GPCLK function of the Raspberry Pi. This has been developed for Raspberry Pi OS, version Bookworm.

## How does it work?

The Raspberry Pi Broadcom-based SoC can generate clock signals from near 0 Hz through a large portion of the UHF spectrum. By modulating this clock signal with [librpitx](https://github.com/F5OEO/librpitx), it is possible to transmit Horus Binary v2 using a GPIO pin on a Raspberry Pi. 

The clock signal generated is a sqaure wave, so moderate filtering should be used before routing the signal to an antenna.

## Supported Hardware

System-on-Chip | Raspbery Pi | RPi TX  Supported
------|------|------
BCM2835 | Model 1 A, A+, B, B+, Zero (W) | :grey_question:
BCM2836 | Model 2 B | :grey_question:
BCM2837 | Model 3 B, CM3 (some 2 B),  | :heavy_check_mark:
BCM2837B0 | Model 3 A+, B+, CM3+ | :heavy_check_mark:
BCM2711 | Model 4 B, CM4, Pi 400 | :grey_question:
BCM2712 | Model 5 B, CM5, Pi 500 | :x:
RP3A0 | Model Zero 2W | :heavy_check_mark:

## Installation

### Native Install

Install required libraries and utilities via `apt`:

```console
sudo apt update
sudo apt install --no-install-recommends git libraspberrypi-dev python3-venv python3-pip
```

Install [librpitx](https://github.com/F5OEO/librpitx) with the following commands: 

```console
git clone https://github.com/F5OEO/librpitx.git
cd librpitx/src/
make
sudo make install
cd ~
```

Install [horusdemodlib](https://github.com/projecthorus/horusdemodlib) with the following commands. The build process is to install `libhorus.so`. Further down in these instructions we will use `pip` to install the complemetary Python library to encode packets. Both are needed. 

```console
git clone https://github.com/projecthorus/horusdemodlib.git
cd horusdemodlib && mkdir build && cd build
cmake ..
make
sudo make install
sudo ldconfig
cd ~
```

Build horusrpitx:

```console
git clone https://github.com/projecthorus/horusrpitx.git
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cd mod
make
cd ..
```

## Transmitting Sample Packets

In some cases it may be useful to generate sample packets to test a receiver and demodulation software, but without the use of a GPS. 

All of the arguments shown below are optional. They are shown with their default values. 

```console
sudo venv/bin/python PacketTX.py --frequency 434.2 --id 256 --lat 0 --lon 0 --alt 0 --sats 3 --verbose
```
NOTE: `sudo` is required for RPiTX to function. 

## Transmitting Position Packets

To transmit position packets, a U-Blox GPS is required. When connected via USB, the default UART for the U-Blox GPS is `/dev/ttyACM0`. 

```console
sudo venv/bin/python tx_gps.py 256 --frequency 434.2 --gps /dev/ttyACM0
```
