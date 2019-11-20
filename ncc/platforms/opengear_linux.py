import re

from netmiko import ConnectHandler


class OpengearLinux():
    CONFIG_SECRETS = [
        (r'(.*password) \S+', r'\1 <secret hidden>'),
        (r'(.*community) \S+', r'\1 <secret hidden>')        
    ]
    GLOBAL_FILTER = []
    DEVICE_TYPE = "linux"
    
    def __init__(self, hide_secrets, **params):
        self.hide_secrets = hide_secrets
        self.netcon = ConnectHandler(
            device_type=self.DEVICE_TYPE,
            host=params["host"], 
            username=params["username"], 
            password=params["password"]
        )
        self.config = self.get_config(hide_secrets)
        self.metadata = self.get_metadata()

    def get_config(self, hide_secrets):
        cfg = self.netcon.send_command("config -g config")

        return self.filter(cfg)

    def get_metadata(self):
        meta = cfg = self.netcon.send_command("cat /etc/version")

        fill = "#" * 10
        meta_data = "{fill} METADATA {fill}\n".format(fill=fill)
        meta = meta.split()
        meta_data += "# platform: {}\n".format(meta[0])
        meta_data += "# sw version: {}\n".format(meta[2])
        meta_data += "{fill} END-METADATA {fill}".format(fill=fill)

        return self.filter(meta_data)

    def filter(self, cfg):

        if self.hide_secrets:
            for secret in self.CONFIG_SECRETS:
                cfg = re.sub(secret[0], secret[1], cfg, flags=re.M)

        for gfilter in self.GLOBAL_FILTER:
            cfg = re.sub(gfilter[0], gfilter[1], cfg, flags=re.M)
        
        return cfg