import os
import logging

import click

from ncc import collect
from ncc import write
from ncc.libs.creds import creds
from ncc.libs.inventory.init_nornir import get_devices

from nornir.plugins.functions.text import print_result


# Configs
repo = "it-netconfigs"
branch ="master"
org = "ctopher78" # github user or org
sites = ["usden1", "usden2", "ussfo1", "uscol1", "uscol2", "uscol3"]
collect_freq = 60 # minutes

failed_hosts = dict()

@click.command()
@click.option(
    "--loglevel",
    "-l",
    default="info",
    type=click.Choice(["info", "debug", "warning"]),
    show_default="info",
    help="Enabled debug logging"
)
@click.option(
    "--console/--no-console",
    "-c",
    default=False,
    show_default="--no-console",
    help="Print logs to stdout"
)
@click.option(
    "--hide-secrets/--show-secrets",
    default=True,
    show_default="--hide-secrets",
    help="Redact sensitive secrets from config files.  Use before pushing to public GitHub Repos"
)
@click.option(
    "--retries",
    "-r",
    default=1,
    show_default=1,
    help="Number of times to retry collecting configs for failed devices"
)
def main(loglevel, console, hide_secrets, retries):
    logging.getLogger("nornir")
    # get inventory
    devices = get_devices(filter="", num_workers=15, loglevel=loglevel, console=console, netbox_token=creds.get_nb_token())

    creds.set_device_defaults(devices)

    # Collect configs for all network devices
    # Shard out work by site to minimize resource issues
    for site in sites:
        logging.info("Collecting configs for: %s", site)

        nornir_obj, results = collect.configs(devices.filter(site=site), hide_secrets, retries)

        write_configs(site, nornir_obj)

        failed_hosts.update(results.failed_hosts)

    # Eventually send message to slack that show
    # which devices we failed to collect configs for
    for h, r in failed_hosts.items():
        print("Execption: ", r[0].exception)
        #print("result: ", r[0].result)

    # Add, commit, and push collected configs to remote
    # repo as new branch.


def write_configs(site, nornir_obj):
    configs = list()

    print("Writing configs")
    for hostname, nr_obj in nornir_obj.inventory.hosts.items():
        if nr_obj.get("configs"):
            config = dict()
            config["path"] = os.path.join(site, hostname+".cfg")
            config["content"] = nr_obj.get("configs")
            config["mode"] = "100644"

            configs.append(config)

    gh = write.Github(creds.get_github_token(), org, repo, branch)
    gh.push(configs)



if __name__ == "__main__":
     main()
