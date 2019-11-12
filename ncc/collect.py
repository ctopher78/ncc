
import logging

from netmiko import ConnectHandler


commands = {
    "cisco_ios": ["show run"]
}


def configs(devices):
    d = devices.filter(platform="opengear")
    r = d.run(task=_collect)



def _collect(task):
    print(task.host)
    if task.host.platform == "opengear":
        task.host.platform = "linux"
    cfg = {
        "device_type": task.host.platform,
        "host": task.host.name,
        "username": task.host.username,
        "password": task.host.password
    }
    print(cfg)
