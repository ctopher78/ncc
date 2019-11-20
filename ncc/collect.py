
import re
import sys
import logging

import xmltodict

from ncc.platforms.cisco_ios import CiscoIOS
from ncc.platforms.cisco_asa import CiscoASA
from ncc.platforms.cisco_wlc import CiscoWLC
from ncc.platforms.cisco_nxos import CiscoNXOS
from ncc.platforms.dell_os6 import DellOS6
from ncc.platforms.juniper_junos import JuniperJunos
from ncc.platforms.paloalto_panos import PaloaltoPanos
from ncc.platforms.opengear_linux import OpengearLinux


class UnsupportedPlatform(Exception):
    pass


class MissingHandler(Exception):
    pass


# Maps Netbox Platfrom field to ncc platform Class
platform_map = {
    "ios": CiscoIOS,
    "nxos": CiscoNXOS,
    "asa": CiscoASA,
    "cisco_wlc": CiscoWLC,
    "panos": PaloaltoPanos,
    "opengear": OpengearLinux,
    "junos": JuniperJunos,
    "dell_os6": DellOS6,
}


faild_hosts = list()

# logging.basicConfig(filename="test1.txt", level=logging.DEBUG)
# logger = logging.getLogger("netmiko")


def configs(devices, hide_secrets, retries):
    results = devices.run(task=_collect, hide_secrets=hide_secrets)

    retried = 0
    if results.failed and retried < retries:
        r = devices.run(task=_collect, on_failed=True, on_good=False, hide_secrets=hide_secrets)
        retried += 1

    return devices, results


def _collect(task, hide_secrets):
    platform = task.host.platform

    if platform not in platform_map.keys():
        raise UnsupportedPlatform("'{}' not in {}".format(platform, platform_map.keys()))

    device_type = platform_map[platform]
    
    params = {
        "platform": platform,
        "host": task.host.hostname,
        "username": task.host.username,
        "password": task.host.password
    }

    netcon = connect(hide_secrets, params)

    task.host["configs"] = netcon.metadata
    task.host["configs"] += netcon.config


def connect(hide_secrets, conn_params):
    return platform_map[conn_params["platform"]](hide_secrets, **conn_params)




