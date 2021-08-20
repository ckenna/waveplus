#!/usr/bin/env python3

import logging
import struct

from contextlib import contextmanager
from dataclasses import dataclass, field, InitVar, asdict
from typing import Tuple

import click
import graphyte 
from tenacity import (retry, wait_fixed, stop_after_attempt,
        before_sleep, before_sleep_log)
from bluepy.btle import UUID, Peripheral

WAVE_UUID = UUID("b42e2a68-ade7-11e4-89d3-123b93f75cba")

logger = logging.getLogger(__name__)


@contextmanager
def wave_plus_peripheral(mac_address):
    wave_plus = None
    try:
        wave_plus = Peripheral(mac_address)
        yield wave_plus
    finally:
        if wave_plus is not None:
            wave_plus.disconnect()


@dataclass(frozen=True)
class Sensors:
    """Class to decode and hold sensor information.

    The units are:

    * humidity: %rH
    * accel: unknown
    * light: unknown
    * short and long term average radon levels: Bq/m3
    * temperature: degrees C
    * relative atmospheric pressure: hPa
    * CO2: ppm
    * VOC: ppb

    """

    raw_value: InitVar[Tuple[int, int, int, int, int, int,
        int, int, int, int, int, int]]
    version: float = field(init=False)
    humidity: float = field(init=False)
    light: float = field(init=False)
    accel: float = field(init=False)
    radon_short_term_average: float = field(init=False)
    radon_long_term_average: float = field(init=False)
    temperature: float = field(init=False)
    pressure: float = field(init=False)
    carbon_dioxide_level: float = field(init=False)
    voc_level: float = field(init=False)

    @staticmethod
    def convert_radon(raw_value):
        if raw_value < 0 or raw_value > 16383:
            raise ValueError('Invalid radon level %s.'.format(raw_value))
        return raw_value

    def __post_init__(self, r):
        super().__setattr__('version', r[0])
        if self.version != 1:
            raise ValueError('Unknown sensor version: %s'.format(
                self.version))

        super().__setattr__('humidity', r[1] / 2.0)
        super().__setattr__('light', r[2])
        super().__setattr__('accel', r[3])
        super().__setattr__('radon_short_term_average',
                self.convert_radon(r[4]))
        super().__setattr__('radon_long_term_average', self.convert_radon(r[5]))
        super().__setattr__('temperature', r[6] / 100.0)
        super().__setattr__('pressure', r[7] / 50.0)
        super().__setattr__('carbon_dioxide_level', float(r[8]))
        super().__setattr__('voc_level', float(r[9]))


class WavePlus:
    def __init__(self, mac):
        self.mac = mac

    @retry(wait=wait_fixed(2),
            stop=stop_after_attempt(8),
            before_sleep=before_sleep_log(logger, logging.WARNING))
    def get_data(self):
        with wave_plus_peripheral(self.mac) as wave_plus:
            characteristics = wave_plus.getCharacteristics(uuid=WAVE_UUID)
            raw_data = characteristics[0].read()
            raw_data = struct.unpack('BBBBHHHHHHHH', raw_data)
            return raw_data


@click.command()
@click.option('--log-level', default='info', help='Log level.',
        type=click.Choice(['critical', 'error', 'warning', 'info', 'debug']))
@click.option('--graphite-port', help='Port for Graphite.', default=2003)
@click.option('--graphite-dryrun/--no-graphite-dryrun', default=False,
        help='Do not actually send to Graphite.')
@click.argument('mac')
@click.argument('graphite_host')
@click.argument('graphite_prefix')
def main(log_level, graphite_port, graphite_dryrun, mac, graphite_host,
        graphite_prefix):

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(log_level))
    logging.basicConfig(level=numeric_level)

    graphyte.init(graphite_host, port=graphite_port, prefix=graphite_prefix)

    wave_plus = WavePlus(mac)
    data = wave_plus.get_data()
    sensors = Sensors(data)

    metrics_dict = asdict(sensors)
    del metrics_dict['version']  # do not care about version
    logger.debug('Metrics: %s', metrics_dict)

    for key, value in metrics_dict.items():
        if not graphite_dryrun:
            graphyte.send(key, value)
        else:
            logger.warning('Dry-run: Not sending {}={}'.format(key, value))

if __name__ == '__main__':
    main()
