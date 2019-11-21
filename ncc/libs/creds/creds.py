
import os
import getpass

def set_device_defaults(devices):
    """ Check for username and password env vars first.  If those
    don't exist, then prompt user for creds.  Creds are set in nornir's
    inventory defafaults.  See:
    https://nornir.readthedocs.io/en/latest/howto/transforming_inventory_data.html#Setting-a-default-password
    """
    
    username = os.environ.get("NETUSER")
    password = os.environ.get("NETPASS")

    if not username:
        uname = input(
            "\nPlease enter username (or set `export NETUSER=<your_username>` to avoid this message): "
        )
        username = uname

    if not password:
        pwd = getpass.getpass(
            "\nPlease enter password (or set `export NETPASS=<your_username>` to avoid this message): "
        )
        password = pwd

    devices.inventory.defaults.username = username
    devices.inventory.defaults.password = password


def get_nb_token():
    "Retrieve Netbox API token from env var or Vault"

    token = os.environ.get("NB_TOKEN")

    if not token:
         token = getpass.getpass(
            "\nPlease enter netbox token (or set `export NB_TOKEN=<token>` to avoid this message): "
        )       

    return token


def get_github_token():
    "Retrieves Github Token from env var or Vault"

    token = os.environ.get("GH_TOKEN")

    if not token:
         token = getpass.getpass(
            "\nPlease enter netbox token (or set `export GH_TOKEN=<token>` to avoid this message): "
        )       

    return token