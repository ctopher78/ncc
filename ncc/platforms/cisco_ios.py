import re

import napalm


class CiscoIOS():
    CONFIG_SECRETS = [
        (r'(snmp-server community).*', r'\1 <configuration removed>'),
        (r'(snmp-server host \S+( vrf \S+)?( version (1|2c|3))?)\s+\S+((\s+\S*)*)\s*', r'\1 <secret hidden> \5'),
        (r'(\s+(?:password|secret)) (?:\d )?\S+', r'\1 <secret hidden>'),       
        (r'(username .+ (password|secret) \d) .+', r'\1 <secret hidden>'),
        (r'(enable (password|secret)( level \d+)? \d) .+', r'\1 <secret hidden>'),
        (r'(.*wpa-psk ascii \d) (\S+)', r'\1 <secret hidden>'),
        (r'(.*key 7) (\d.+)', r'\1 <secret hidden>'),
        (r'(tacacs-server (.+ )?key) .+', r'\1 <secret hidden>'),
        (r'(crypto isakmp key) (\S+) (.*)', r'\1 <secret hidden> \3'),
        (r'(\s+ip ospf message-digest-key \d+ md5) .+', r'\1 <secret hidden>'),
        (r'(\s+ip ospf authentication-key) .+', r'\1 <secret hidden>'),
        (r'(\s+neighbor \S+ password) .+', r'\1 <secret hidden>'),
        (r'(\s+vrrp \d+ authentication text) .+', r'\1 <secret hidden>'),
        (r'(\s+standby \d+ authentication) .{1,8}$', r'\1 <secret hidden>'),
        (r'(\s+standby \d+ authentication md5 key-string) .+?( timeout \d+)?$', r'\1 <secret hidden> \2'),
        (r'(\s+key-string) .+', r'\1 <secret hidden>'),
        (r'((tacacs|radius) server [^\n]+\n(\s+[^\n]+\n)*\s+key) [^\n]+$', r'\1 <secret hidden>'),
        (r'(\s+ppp (chap|pap) password \d) .+', r'\1 <secret hidden>'),
    ]
    GLOBAL_FILTER = [
        (r'.*(U|u)ptime .*', r''),
        (r'System re.*', r''),
        (r'Configuration last modified .*', r''),
        (r'Current configuration :.*', r''),
        (r'Last configuration.*', r''),
        (r'NVRAM config last.*', r'')
    ]

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
        cfg = self.netcon.cli(["show run"])["show run"]

        return self.filter(cfg)

    def get_metadata(self):
        results = dict()
        meta_cmds = ["show inventory", "show version"]

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