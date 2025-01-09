# Horus Binary Telemetry Transmitter

Transmit Horus Binary v2 using the GPCLK function of the Raspberry Pi.

## How does it work?

The Raspberry Pi Broadcom-based SoC can generate clock signals from near 0 Hz through a large portion of the UHF spectrum. By modulating this clock signal with [librpitx](https://github.com/F5OEO/librpitx), it is possible to transmit Horus Binary v2 using a GPIO pin on a Raspberry Pi. 

The clock signal generated is a sqaure wave, so moderate filtering should be used before routing the signal to an antenna.

## Installation

Install [librpitx](https://github.com/F5OEO/librpitx) with the following commands: 

```console
sudo apt update
sudo apt install git libraspberrypi-dev
git clone https://github.com/F5OEO/librpitx.git
cd librpitx/src/
make
sudo make install
```

TODO: Insert instructions about horusdemodlib here

Install horusrpitx:

```console
git clone https://github.com/projecthorus/horusrpitx.git
cd src/mod/
make
```

## 