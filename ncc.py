import logging

import click

from ncc import collect
from ncc.libs.creds import creds
from ncc.libs.inventory.init_nornir import get_devices




# Configs
log = "/path-to-log"
save_path = "/path-to-configs-git-repo"
sites = ["usden1", "usden2", "ussfo1", "uscol1", "uscol2", "uscol3"]
collect_freq = 60 # minutes


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
def main(loglevel, console):
    logging.getLogger("nornir")
    # get inventory
    devices = get_devices(filter="", num_workers=5, loglevel=loglevel, console=console, netbox_token=creds.get_nb_token())

    creds.set_device_defaults(devices)

    # Shard out work by site to minimize resource issues
    # log getting {site} configs
    for site in sites:
        logging.info("Collecting configs for: %s", site)

        results = collect.configs(devices.filter(site=site))


    # redact configs
    # write configs to local git directory
    # git add ; git commit; git push to branch 
        # I might make this a separate cron job so we don't get innundated with PR's


if __name__ == "__main__":
     main()