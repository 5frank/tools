#!/usr/bin/env python3
import argparse
import subprocess
import os
import glob
import re
import sys
from datetime import datetime, timezone
from pprint import pprint
from typing import List, Dict, Optional
from difflib import SequenceMatcher

VERBOSE = 0
VERSION = 0.3


def print_dbg(*args):
    if VERBOSE > 0:
        print("DBG:", *args, file=sys.stderr)


def print_err(*args):
    print("ERR:", *args, file=sys.stderr)


def print_wrn(*args):
    print("WRN:", *args, file=sys.stderr)


def fuzzy_match(s1, s2):
    """Compare two strings and return similarity ratio (0.0 to 1.0)"""
    return SequenceMatcher(None, s1, s2).ratio()

def timestamp_to_iso8601(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


class UsbHistory:
    """
    Class for querying USB device history from systemd journal logs.
    """

    def __init__(self, since="boot", until=None):
        self.entries = {}
        self.load(since, until)

    def _assert_journal_permission(self):
        # verification: Try a dry-run of journalctl
        # We check if journalctl returns a specific hint about permissions
        cp = subprocess.Popen(
            ['journalctl', '-n', '0'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        _, stderr = cp.communicate()

        if "not seeing messages" in stderr:
            print_err("Insufficient permissions to read journalctl.")
            sys.exit(1)

    def _port_from_journal_entry(self, entry):
        """
        assume entry has '_KERNEL_SUBSYSTEM=usb'
        """
        message = entry.get("MESSAGE")
        kdev = entry.get("_KERNEL_DEVICE")
        # _KERNEL_DEVICE is VID:PID 'c189:122' or port 'usb 1-4.4.3:'
        if not kdev is None:
            match = re.search(r'usb:([\d.-]+(?::[\d.]+)?)', kdev)
            if match:
                port = match.group(1)
                return port
            else:
                print_dbg("failed to get port from _KERNEL_DEVICE: '{}'".format(kdev), message)

        assert message is not None
        match = re.search(r'^usb\s+([\d.-]+)', message)
        if not match:
            print_wrn("failed to get port from: '{}'".format(message))
            return None

        port = match.group(1)
        return port

    def load(self, since="boot", until=None):
        import json

        cmd = ['journalctl', '-k',
               '-n', '100',
               '-o', 'json',
               '_KERNEL_SUBSYSTEM=usb']

        if since == "boot":
            cmd.append("-b")
        elif since:
            cmd.extend(['--since', since])

        if until:
            cmd.extend(['--until', until])

        try:
            # Run journalctl
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print_err("Error running journalctl: %s", e)
            return
        except FileNotFoundError:
            print_err("journalctl not found. Is this a systemd-based system?")
            return
        lines = res.stdout.splitlines()
        # journalctl returns 0 even when it has permission issues - it just returns empty output.
        if not lines:
            self._assert_journal_permission()

        d = {}
        for line in lines:
            entry = json.loads(line)
            message = entry.get("MESSAGE")
            if not message:
                print_wrn("no MESSAGE in journal entry:", line)
                continue

            devnode = entry.get("_UDEV_DEVNODE")
            if not devnode:
                print_dbg("no _UDEV_DEVNODE in entry:", message)
                continue

            # __REALTIME_TIMESTAMP in unit: Microseconds since Unix epoch
            ts = entry.get("__REALTIME_TIMESTAMP")
            assert ts is not None
            ts = int(ts) / 1e6

            port = self._port_from_journal_entry(entry)
            if devnode not in d:
                d[devnode] = {
                    'ts_first': ts,
                    'ts_last': ts,
                    'messages': [],
                    'devnode': devnode,
                    'port': port
                }

            else:
                """
                if d[devnode]['port'] is None:
                    # same devnode - assume same port?
                    d[devnode]['port'] = port
                """
                if d[devnode]['port'] != port:
                    print_wrn(devnode, ":", d[devnode]['port'], "!=", port)
                    continue

                if ts < d[devnode]['ts_first']:
                    d[devnode]['ts_first'] = ts
                elif ts > d[devnode]['ts_last']:
                    d[devnode]['ts_last'] = ts

                """
                ts_delta = d[devnode]['timestamp'] - ts
                if abs(ts_delta) > 5*60:
                    print_wrn(devnode, ":", "timestamp delta on message is", ts_delta, "sec")
                    continue
                """

            props = self._property_from_msg(message)
            if props:
                # cumsume this line
                d[devnode].update(props)
            else:
                d[devnode]['messages'].append(message)

        self.entries = d

    def _property_from_msg(self, msg):
        ret = {}
        # Dict of (prefix_for_fast_check, regex_pattern)
        patterns = {
            'Manufacturer': ('Manufacturer:', r'Manufacturer:\s*(\S+.*)'),
            'Product': ('Product:', r'Product:\s*(.+)'),
            'SerialNumber': ('SerialNumber:', r'SerialNumber:\s*(\S+)'),
            'idVendor': ('idVendor=', r'idVendor=([0-9a-fA-F]+)'),
            'idProduct': ('idProduct=', r'idProduct=([0-9a-fA-F]+)'),
        }

        for k, (prefix, expr) in patterns.items():
            if prefix not in msg:
                continue

            match = re.search(expr, msg)
            if not match:
                print_dbg(f"Pattern '{expr}' didn't match in: {msg}")
                continue

            ret[k] = match.group(1).strip()

        return ret

    def id_name_from_entry(self, entry):
        """
        Build device ID name from already parsed entry fields.

        Returns:
            str: device ID like "usb-Manufacturer_Product_SerialNumber"
        """
        manufacturer = entry.get('Manufacturer', '').replace(' ', '_')
        product = entry.get('Product', '').replace(' ', '_')
        serial = entry.get('SerialNumber', '')

        parts = (manufacturer, product, serial)
        return 'usb-' + '_'.join(parts)

    def filter_by_device(self, device):
        """
        Filter log entries matching a speculative device path. example:
        /dev/serial/by-id/usb-manufacturer_product_serial-if00

        """
        dev_basename = os.path.basename(device)
        matches = {}

        for devnode, entry in self.entries.items():
            id_name = self.id_name_from_entry(entry)

            if not id_name:
                continue
            m = fuzzy_match(dev_basename, id_name)
            print_dbg("match: {:.2f}  with: '{}'".format(m, id_name))

            if m >= 0.6:
                matches[devnode] = entry
                continue

        return matches

    def filter_by_properties(self, properties):
        """
        Filter log entries matching given properties (manufacturer, serial,
        idVendor, idProduct, etc.)

        """
        if not properties:
            return {}

        ret = {}

        for devnode, entry in self.entries.items():

            for key, value in properties.items():
                if not key in entry:
                    continue
                if entry[key] != value:
                    continue
                ret[devnode] = entry

        return ret

    def get_entries(self):
        """
        Get all loaded entries.

        Returns:
            dict: all entries with devnode as key
        """
        return self.entries

    def pprint_entries(self, entries):

        for devnode, entry in entries.items():
            self.pprint_entry(entry)

    def pprint_entry(self, entry, lnpre="   "):

        print("====", entry['devnode'], "====")
        k_order = ['devnode', 'port', 'ts_first', 'ts_last']

        for k in ['ts_first', 'ts_last']:
            entry[k] = timestamp_to_iso8601(entry[k])

        # Print ordered keys first
        for k in k_order:
            if k in entry:
                print(lnpre, f"{k}: {entry[k]}")

        # Print remaining keys
        for k, v in entry.items():
            if k not in k_order:
                if isinstance(v, list):
                    print(lnpre, f"{k}:")
                    for item in v:
                        print(lnpre, f"  - {item}")
                else:
                    print(lnpre, f"{k}: {v}")
        print()  # blank line between entries




def syspath_from_dev(dev):
    cmd = ["udevadm", "info",
           "--name", dev,
           "--query", "path"
           ]

    result = subprocess.run(cmd,
                            check=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True)

    if result.returncode != 0:
        print_err("udevadm failed with exit status ",
                  result.returncode, ". ", result.stderr)
        return None

    print_dbg(result)
    syspath = result.stdout.strip()
    if syspath:
        return "/sys/" + syspath


def find_first_up(path, name):
    while path != "/":
        # Build find command
        cmd = ["find", path, "-maxdepth", "1", "-mindepth",
               "1", "-name", name, "-print", "-quit"]
        try:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, universal_newlines=True)
            out = result.stdout.strip()
            if out:
                return out
        except Exception as e:
            print_err("find_first_up:", e)
        # Move up a directory
        path = os.path.realpath(os.path.join(path, ".."))
    return None


def search_properties(syspath, properties):
    matches = []
    for fname, val in properties.items():
        fpath = os.path.join(syspath, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                contents = f.read()
                if re.search(re.escape(val), contents, re.IGNORECASE):
                    matches.append(fname)
        except Exception as e:
            print_dbg("search_properties error:", fpath, e)
    return matches


def syspath_from_properties(properties):
    num_properties = len(properties.keys())
    found = []

    for bus in glob.glob("/sys/bus/usb/devices/usb*/"):
        for dirpath, _, files in os.walk(bus):
            if not "dev" in files:
                continue
            sysdir = os.path.abspath(dirpath)
            matches = search_properties(sysdir, properties)
            if not matches:
                continue
            if len(matches) == num_properties:
                print_dbg(f"{sysdir} - matches ({','.join(matches)})")
                found.append(sysdir)
    return found


def usbport_from_syspath(syspath):
    port = find_first_up(syspath, name="port")
    if not port:
        print_err(f"No port file found in parent directories from {syspath}")
        sys.exit(1)
    # print_dbg("portdir:", port)
    port = os.path.realpath(port)
    print_dbg("extractinc hub location and port from:", port)
    # Extract info for uhubctl
    # basename could be "1-1.5-port3", "usb1-port1" or 1-1.5.3"
    bname = os.path.basename(port)
    bname = re.sub(r"-port", " ", bname)
    bname = re.sub(r"^usb", "", bname)
    hubport = bname.split(" ")
    assert len(hubport) == 2
    hub = hubport[0]
    port = hubport[1]
    return hub, port


DESCRIPTION="Find physical USB port of a device or from device properties"

EPILOG = """
Find physical USB port of a device. 
Default output format is: '<bus>-<port[.port]>.port port'. Examples:
    '1 2' bus=usb1 device on port 2.
    '1-2.3 4' bus=usb1. two usb hubs on port 2 then 3. Device on port 4.

If options result in multiple matching ports will exit with non zero exit status. 

Remarks:
    Not all devices connected to a USB port might have a device file.
    A single USB port migh have several device files of different types.


Other useful commands:
    lsusb verbose tree view will show device in /sys/bus/usb/
    `lsusb -tvv` 
    
    info of device:
    `udevadm info --name=/dev/ttyUSB0 --attribute-walk`

    turn usb port power off:
    `sudo uhubctl --location=1-1 --port=7 --action=off`
"""


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    # Dummy class used to remove automatic linewrapping of EPILOG
    pass


def parse_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG,
                                     formatter_class=CustomFormatter)

    parser.add_argument("-v", "--verbose", action="count",
                        default=0, help="Enable verbose output")

    parser.add_argument("-H", "--history", action="store_true", default=False,
                        help="Retrive possible disconnected device from log")

    parser.add_argument("-S", "--since", dest="since",
                        help="Show entries since specified time "
                        "(journalctl format, e.g., '2 hours ago', '2024-01-01')")

    parser.add_argument("-U", "--until", dest="until",
                        help="Show entries until specified time (journalctl format)")

    parser.add_argument("--dev", "--device", dest="device",
                        help="Device file connected to USB. "
                        "This will ignore other property options such as vid and pid")

    parser.add_argument("--vid", "--idvendor",
                        dest="idVendor",
                        help="USB vendor ID. (hex format, case insensitive). "
                        "use '.' for any digit. ")

    parser.add_argument("--pid", "--idproduct",
                        dest="idProduct",
                        help="USB product ID. (hex format, case insensitive). "
                        "use '.' for any digit. ")

    parser.add_argument("--serial", dest="serial", help="USB product ID")

    parser.add_argument("--format", choices=["uhubctl"],
        help="Output format. `uhubctl` - hub and port formated as options accepted by uhubctl. "
        "Example `--location=1.2 --port=3`")

    parser.add_argument("--mfg", "--manufacturer", dest="manufacturer",
                        help="Device manufacturer name")
    args, extra = parser.parse_known_args()
    return args


def cmd_history(args, properties):
    since = getattr(args, 'since', None) or "boot"
    until = getattr(args, 'until', None)

    history = UsbHistory(since=since, until=until)

    if args.device:
        d = history.filter_by_device(args.device)
    elif properties:
        d = history.filter_by_properties(properties)
    else:
        d = history.get_entries()

    history.pprint_entries(d)


def cmd_default(args, properties):
    syspath = None

    if args.device:
        syspath = syspath_from_dev(args.device)
        if not syspath:
            sys.exit(1)
    elif properties:
        syspaths = syspath_from_properties(properties)
        if not syspaths:
            print_err("Failed to find any matching path in /sys/")
            sys.exit(1)
        if len(syspaths) > 1:
            print_err("Found more than one matching ports")
            sys.exit(1)
        syspath = syspaths[0]
    else:
        print_err("missing options for device or device properties")
        sys.exit(1)

    print_dbg("syspath(s):", syspath)
    hub, port = usbport_from_syspath(syspath)

    if args.format == "uhubctl":
        output = "--location={} --port={}".format(hub, port)
    else:
        output = "{} {}".format(hub, port)

    print(output)
    return 0


def main():
    global VERBOSE
    args = parse_args()

    # if args.help:
    #    sys.exit(0)
    VERBOSE = args.verbose
    properties = {}

    prop_keys = ["idVendor", "idProduct", "manufacturer", "serial"]
    for k in prop_keys:
        val = getattr(args, k)
        if val:
            properties[k] = val

    print_dbg("properties:", properties)

    if args.history:
        return cmd_history(args, properties)
    else:
        return cmd_default(args, properties)


if __name__ == "__main__":
    main()
