import re

from netmiko import ConnectHandler


class CiscoWLC():
    CONFIG_SECRETS = []
    GLOBAL_FILTER = [
        (r'OUI File Update Time.*', r''),
        (r'System Up Time.*', r''),
        (r'Operating Environment.*', r''),
        (r'Internal Temperature.*', r''),
        (r'Number of WLANs.*', r''),
        (r'Number of Active Clients.*', r'')
    ]
    DEVICE_TYPE = "cisco_wlc_ssh"
    
    # BANNER_TIMEOUT is a netmiko arg that is required for 
    # connecting to Cisco WLC
    BANNER_TIMEOUT = 10

    def __init__(self, hide_secrets, **params):
        self.hide_secrets = hide_secrets
        self.netcon = ConnectHandler(
            device_type=self.DEVICE_TYPE,
            host=params["host"], 
            username=params["username"], 
            password=params["password"],
            banner_timeout=self.BANNER_TIMEOUT
        )
        self.config = self.get_config(hide_secrets)
        self.metadata = self.get_metadata()

    def get_config(self, hide_secrets):
        cfg = self.netcon.send_command("show run-config commands")

        return self.filter(cfg)

    def get_metadata(self):
        results = dict()
        meta_cmds = ["show inventory", "show sysinfo"]
        for cmd in meta_cmds:
            results[cmd] = self.netcon.send_command(cmd)
        
        fill = "#" * 10
        meta_data = "{fill} METADATA {fill}\n".format(fill=fill)
        for cmd, result in results.items():
            meta_data += "\n\n{}\n{}{}".format(cmd, "-"*15, result)
        meta_data += "\n{fill} END-METADATA {fill}".format(fill=fill)
        
        # add comment '#' at the beginning of each line.
        meta_data = re.sub(r'^(.*)', r'# \1', meta_data, flags=re.M)
        
        return self.filter(meta_data)

    def filter(self, cfg):
        if self.hide_secrets:
            for secret in self.CONFIG_SECRETS:
                cfg = re.sub(secret[0], secret[1], cfg, flags=re.M)

        for gfilter in self.GLOBAL_FILTER:
            cfg = re.sub(gfilter[0], gfilter[1], cfg, flags=re.M)
        
        return cfg