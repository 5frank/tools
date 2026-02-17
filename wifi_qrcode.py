#qrencode -t utf8 'WIFI:S:Tux;T:WPA;P:thelinuxexperiment.com;;'

import sys
from subprocess import run, PIPE

# Maps nmcli key-mgmt values to WiFi QR code spec security type (T: field)
KEY_MGMT_TO_QR = {
    "wpa-psk":    "WPA",     # WPA/WPA2 Personal
    "wpa-eap":    "WPA",     # WPA/WPA2 Enterprise
    "sae":        "WPA",     # WPA3 Personal
    "ieee8021x":  "WEP",     # Dynamic WEP
    "none":       "nopass",  # Open network
}


def wifi_credentials(ssid):
    """Get WiFi credentials for a saved NetworkManager connection by SSID.

    Requires sudo/root to read secrets.
    Returns (ssid, password, key_mgmt) where password may be None for open
    networks, and key_mgmt is e.g. 'wpa-psk', 'wpa-eap', 'none', or ''.
    """
    r = run(["sudo", "nmcli", "-s", "-g",
             "802-11-wireless-security.key-mgmt,802-11-wireless-security.psk,802-1x.password",
             "connection", "show", ssid],
            stdout=PIPE, check=True)
    lines = r.stdout.decode().splitlines()
    key_mgmt = lines[0].strip() if len(lines) > 0 else ""
    psk      = lines[1].strip() if len(lines) > 1 else ""
    eap_pass = lines[2].strip() if len(lines) > 2 else ""

    if key_mgmt == "wpa-psk":
        password = psk or None
    elif key_mgmt == "wpa-eap":
        password = eap_pass or None
    else:
        password = None  # open network

    return (ssid, password, key_mgmt)


def current_ssid():
    """Return the SSID of the currently active WiFi connection, or None."""
    r = run(["nmcli", "-g", "active,ssid", "device", "wifi"],
            stdout=PIPE, check=True)
    for line in r.stdout.decode().splitlines():
        # -g escapes literal colons with '\'; split on unescaped ':'
        parts = line.replace("\\:", "\x00").split(":", 1)
        if len(parts) == 2 and parts[0] == "yes":
            return parts[1].replace("\x00", ":")
    return None


def qrencode(ssid, password, security="WPA2"):
    data = "WIFI:S:{};T:{};P:{};;".format(ssid, security, password)
    cmd = ["qrencode", 
           "--type", "utf8", data.encode()]
    run(cmd, check=True)
    # r = run(cmd, stdout=PIPE, check=True)
    # s = r.stdout.decode()
    # n = s.split()[0]
    # return int(n)

def _test():
    ssid = current_ssid()
    print("current ssid:", ssid)
    r = wifi_credentials(ssid)
    print(r)

def main():

    ssid = current_ssid()
    ssid, password, key_mgmt = wifi_credentials(ssid)
    security = KEY_MGMT_TO_QR[key_mgmt]
    print("==== WiFi ssid:", ssid, "====")
    qrencode(ssid, password, security)

if __name__ == '__main__':
    main()
