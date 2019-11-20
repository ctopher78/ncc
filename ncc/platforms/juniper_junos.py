import re

import napalm


class JuniperJunos():
    CONFIG_SECRETS = [
        (r'(.*) "\S+"; ## SECRET-DATA', r'\1 < secret hidden >'),
        (r'community \S+ \{', r'community < secret hidden >')
    ]
    GLOBAL_FILTER = []

    def __init__(self, hide_secrets, **params):
        self.hide_secrets = hide_secrets
        self.netcon = self.get_napalm_netcon(**params)
        self.config = self.get_config(hide_secrets)
        self.metadata = self.get_metadata()

    def get_napalm_netcon(self, platform, host, username, password):
        driver = napalm.get_network_driver(platform)
        
        device = driver(hostname=host, username=username, password=password)
        device.open()

        return device

    def get_config(self, hide_secrets):
        cfg = self.netcon.cli(["show configuration"])["show configuration"]

        return self.filter(cfg)

    def get_metadata(self):
        results = dict()
        meta_cmds = [
            "show chassis hardware", 
            "show version", 
            "show system license", 
            "show system license keys"
            ]

        results = self.netcon.cli(meta_cmds)

        fill = "#" * 10
        meta_data = "{fill} METADATA {fill}\n".format(fill=fill)
        for cmd, result in results.items():
            meta_data += "\n\n{}\n{}\n{}".format(cmd, "-"*15, result)
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