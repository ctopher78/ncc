import os
import re
from typing import Any, Dict, Optional

from nornir.core.deserializer.inventory import Inventory, HostsDict

import requests


class MissingRequiredDeviceField(Exception):
    "Error raised when Netbox object is missing required keys."
    pass


# Option to deal with WLC
# ssh banner timeouts
netmiko_conn_options = {
    "netmiko": {
        "extras": {
            "banner_timeout": 20
        }
    }
}


def required_keys_check(device_obj):
    required = ["platform", "primary_ip"]

    for i in required:
        if not device_obj.get(i):
            raise MissingRequiredDeviceField("  '{}' netbox object is missing '{}' field.\n\nPlease update netbox with this field to continue.".format(device_obj["name"], i))


class NBInventory(Inventory):
    def __init__(
        self,
        nb_url: Optional[str] = None,
        nb_token: Optional[str] = None,
        use_slugs: bool = True,
        flatten_custom_fields: bool = True,
        filter_parameters: Optional[Dict[str, Any]] = None,
        requests_verify=True,
        **kwargs: Any,
    ) -> None:
        """
        Netbox plugin
        Arguments:
            nb_url: Netbox url, defaults to http://localhost:8080.
                You can also use env variable NB_URL
            nb_token: Netbokx token. You can also use env variable NB_TOKEN
            use_slugs: Whether to use slugs or not
            flatten_custom_fields: Whether to assign custom fields directly to the host or not
            filter_parameters: Key-value pairs to filter down hosts
        """
        filter_parameters = filter_parameters or {}

        nb_url = nb_url or os.environ.get("NB_URL", "http://localhost:8080")
        nb_token = nb_token or os.environ.get(
            "NB_TOKEN", "0123456789abcdef0123456789abcdef01234567"
        )
        headers = {"Authorization": "Token {}".format(nb_token)}

        # Create dict of hosts using 'devices' from NetBox
        r = requests.get(
            "{}/api/dcim/devices/?limit=0".format(nb_url),
            headers=headers,
            params=filter_parameters,
            verify=requests_verify,
        )
        r.raise_for_status()
        nb_devices = r.json()

        virtual_chassis_secondary = re.compile(r".*:[a-z]$")
        hosts = {}
        for d in nb_devices["results"]:
            host: HostsDict = {
                "connection_options": {},
                "data": {}
                }

            # Secondary nodes in vc clusters are
            # skipped during automation runs.
            # The first node in the cluster will 
            # represent the entire cluster.
            if virtual_chassis_secondary.search(d["name"]):
                continue
            
            # skip devices not marked for monitorig in Netbox
            if not d["custom_fields"]["monitor"]:
                # Log devices not being monitored
                continue


            # Make sure Netbox objects contain
            # all the necessary keys to proceed
            required_keys_check(d)

            # Cisco WLC needs special connection options
            # Specifically banner_timeout
            # see: https://github.com/ktbyers/netmiko/issues/1314
            if d["platform"]["slug"] == "cisco_wlc":
                host["connection_options"] = netmiko_conn_options

            host["hostname"] = d["primary_ip"]["address"].split("/")[0]
            # Add values that don't have an option for 'slug'
            host["data"]["serial"] = d["serial"]
            host["data"]["vendor"] = d["device_type"]["manufacturer"]["name"]
            host["data"]["asset_tag"] = d["asset_tag"]
            if flatten_custom_fields:
                for cf, value in d["custom_fields"].items():
                    host["data"][cf] = value
            else:
                host["data"]["custom_fields"] = d["custom_fields"]

            # Add values that do have an option for 'slug'
            if use_slugs:
                host["data"]["site"] = d["site"]["slug"]
                host["data"]["role"] = d["device_role"]["slug"]
                host["data"]["model"] = d["device_type"]["slug"]

                # Attempt to add 'platform' based of value in 'slug'
                host["platform"] = d["platform"]["slug"] if d["platform"] else None

            else:
                host["data"]["site"] = d["site"]["name"]
                host["data"]["role"] = d["device_role"]
                host["data"]["model"] = d["device_type"]
                host["platform"] = d["platform"]

            # Assign temporary dict to outer dict
            hosts[d["name"]] = host

        # Pass the data back to the parent class
        super().__init__(hosts=hosts, groups={}, defaults={}, **kwargs)
