import asyncio
import argparse
import logging
import sys
import time
import datetime
import re

#from subprocess import run, PIPE
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

g_devices = {}

args = None
class _Device():
    def __init__(self):
        self.rssi = None
        self.name = None
        self.last_seen = 0
        self.adv_data = None

def time_now():
    return int(time.time())


def refresh_screen():
    global g_devices
    global args
    t_now = time_now()

    # clear screen
    print("\033[2J")
    # move cursor to row 1 column 1
    print("\033[1;1f", end="")

    print("ADDRESS           RSSI NAME")

    devs_sorted = sorted(g_devices, reverse=True, key=lambda k: g_devices[k].rssi)

    for addr in devs_sorted:
        d = g_devices[addr]
        age = t_now - d.last_seen

        if args.history and age > args.history:
            # remove
            g_devices.pop(addr)
            continue


        #age = str(dt).ljust(3)
        line = ""
        line += str(addr) + " "
        #line += "{: <4} ".format(age)
        line += "{: <4} ".format(d.rssi)
        line += d.name
        #line += str(d.adv_data)
        #line += str(age).rjust(3)
        print(line)




parser = argparse.ArgumentParser()

parser.add_argument("-n", "--name",
    type=str,
    default=None,
    help="match name")

parser.add_argument("-a", "--addr",
    type=str,
    default=None,
    help="match address")

parser.add_argument("--history",
    type=int,
    default=5,
    help="History in seconds before devices removed from list")


def _dt_iso8601_compact(dt, usec=False):
    fmt = "%Y%m%dT%H%M%S.%fZ" if usec else "%Y%m%dT%H%M%SZ"

    return dt.strftime(fmt)

def is_match(dev, addr=None):
    global args

    #lambda d, ad: d.name and d.name.lower() == wanted_name.lower()
    if args.name:
        if args.name.lower() == dev.name.lower():
            return True

    if args.addr:
        if args.addr == dev.address:
            return True

    return False


def scanner_callback(dev, adv_data):
    #if not is_match(dev):
    #    return
    #if not is_match(dev):
    #    return

    #update_device(dev)
    #print(dev.address, "RSSI:", dev.rssi, dev.name)

    global g_devices

    if not dev.address in g_devices:
        g_devices[dev.address] = _Device()

    mfg_data = adv_data.manufacturer_data

    g_devices[dev.address].rssi = adv_data.rssi
    g_devices[dev.address].name = dev.name if dev.name else "<?>"
    g_devices[dev.address].last_seen = time_now()
    g_devices[dev.address].adv_data = adv_data




async def _async_main():
    #loop = asyncio.get_event_loop()

    scanner = BleakScanner(scanner_callback)

    await scanner.start()

    try:
        while True:
            await asyncio.sleep(1.0)
            refresh_screen()

    except KeyboardInterrupt:
        pass
    await scanner.stop()

def main():
    global args
    args = parser.parse_args()
    asyncio.run(_async_main())

if __name__ == "__main__":
    main()
