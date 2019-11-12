import os
import sys
import urllib3

from nornir import InitNornir

# from lib.creds import creds_from_env


def _init_nornir(filter, num_workers, loglevel, console):
    """ 
    _init_nornir sets the maximum number of workers (`num_workers`) and
    gathers the inventory of network devices to run against from NetBox using 
    the provided `filter`.  
    """
    # TODO: Temp ignore ssl insecure warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    filter_params = [("tag", "network")]

    filter_params.extend(filter)
    nr = InitNornir(
        core={"num_workers": num_workers},
        logging={"level": loglevel, "to_console": console},
        inventory={
            "plugin": "ncc.libs.inventory.netbox.NBInventory",
            "options": {
                "nb_url": "https://netbox.gustocorp.com",
                "nb_token": netbox_token,
                "filter_parameters": filter_params,  # only pulls devices with `network` tag set.
                "requests_verify": False,  # TODO: Requests library doesn't have access to Gusto CA.  I'll need to research how to add that CA in order to verify nb server.
            },
            #"transform_function": adapt_host_data,
        },
    )

    return nr


def get_devices(filter, num_workers, loglevel, console, netbox_token):
    #ni = _init_nornir(filter, num_workers, loglevel, console)
    """ 
    get_devices sets the maximum number of workers (`num_workers`) and
    gathers the inventory of network devices to run against from NetBox using 
    the provided `filter` and netbox API Key.  
    """
    # TODO: Temp ignore ssl insecure warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    filter_params = [("tag", "network")]

    filter_params.extend(filter)
    nr = InitNornir(
        core={"num_workers": num_workers},
        logging={"level": loglevel, "to_console": console},
        inventory={
            "plugin": "ncc.libs.inventory.netbox.NBInventory",
            "options": {
                "nb_url": "https://netbox.gustocorp.com",
                "nb_token": netbox_token,
                "filter_parameters": filter_params,  # only pulls devices with `network` tag set.
                "requests_verify": False,  # TODO: Requests library doesn't have access to Gusto CA.  I'll need to research how to add that CA in order to verify nb server.
            },
            #"transform_function": adapt_host_data,
        },
    )

    return nr
