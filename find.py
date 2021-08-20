#!/usr/bin/env python3

import logging
import struct

from bluepy.btle import Scanner

logger = logging.getLogger(__name__)

# https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers/
# 820 (0x0334) is Corentium AS, which makes Airthings.
COMPANY_ID = 820

def main():
    logging.basicConfig(level=logging.INFO)

    scanner = Scanner()
    scan_entries = scanner.scan(5)

    # https://ianharvey.github.io/bluepy-doc/scanentry.html
    for scan_entry in scan_entries:
        for adtype, description, value in scan_entry.getScanData():
            if 'Manufacturer' == description:
                value_arr = bytearray.fromhex(value)
                company_base_ten = (value_arr[1] << 8) | value_arr[0]
                if COMPANY_ID != company_base_ten:
                    continue  # Probably not an Airthings
                logging.info('Found a potential Airthings with MAC address: %s', scan_entry.addr)


if __name__ == '__main__':
    main()
