import re

import json
import xmltodict
import pandevice.firewall


class PaloaltoPanos():
    CONFIG_SECRETS = [
        (r'(phash":) "\S+(,?)', r'\1 <secret hidden>\2'),
        (r'("(?:private-)?key":) "\S+(,?)', r'\1 <secret hidden>'),
        (r'("bind-password":) "\S+', r'\1 <secret hidden>')
    ]
    GLOBAL_FILTER = []
    
    def __init__(self, hide_secrets, **params):
        self.hide_secrets = hide_secrets
        self.netcon = pandevice.firewall.Firewall(params["host"], params["username"], params["password"])
        self.config = self.get_config(hide_secrets)
        self.metadata = self.get_metadata()
        
    def get_config(self, hide_secrets):
        xml_cfg = self.netcon.op("show config running", xml=True)
        json_cfg = json.dumps(xmltodict.parse(xml_cfg)["response"]["result"]["config"], indent=2)

        return self.filter(json_cfg)

    def get_metadata(self):
        xml_data = self.netcon.op("show system info", xml=True)
        info = xmltodict.parse(xml_data)["response"]["result"]["system"]

        fill = "#" * 10
        meta_data = "{fill} METADATA {fill}\n".format(fill=fill)
        print_fields = ["hostname", "ip-address", "netmask", "default-gateway",
                        "ip-assignment", "mac-address", "family", "model", "serial"
                        "sw-version", "vpn-disable-mode", "multi-vsys", "operational-mode"]

        for name, value in info.items():
            if name in print_fields:
                meta_data += "# {}: {}\n".format(name, value)
        meta_data += "{fill} END-METADATA {fill}".format(fill=fill)

        return meta_data

    def filter(self, cfg):
        if self.hide_secrets:
            for secret in self.CONFIG_SECRETS:
                cfg = re.sub(secret[0], secret[1], cfg, flags=re.M)

        for gfilter in self.GLOBAL_FILTER:
            cfg = re.sub(gfilter[0], gfilter[1], cfg, flags=re.M)
        
        return cfg