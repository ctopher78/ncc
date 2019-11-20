import re

from netmiko import ConnectHandler


class CiscoASA():
    CONFIG_SECRETS = [
        (r'enable password (\S+) (.*)', r'enable password <secret hidden> \2'),
        (r'^passwd (\S+) (.*)', r'passwd <secret hidden> \2'),
        (r'username (\S+) password (\S+) (.*)', r'username \1 password <secret hidden> \3'),
        # ('(ikev[12] ((remote|local)-authentication )?pre-shared-key) (\S+)', '\1 <secret hidden>'),
        # ('^(aaa-server TACACS\+? \(\S+\) host[^\n]*\n(\s+[^\n]+\n)*\skey) \S+$', '\1 <secret hidden>'),
        # ('^(aaa-server \S+ \(\S+\) host[^\n]*\n(\s+[^\n]+\n)*\s+key) \S+$', '\1 <secret hidden>'),
        # ('ldap-login-password (\S+)', 'ldap-login-password <secret hidden>'),
        # ('^snmp-server host (.*) community (\S+)', 'snmp-server host \1 community <secret hidden>'),
        # ('^(failover key) .+', '\1 <secret hidden>'),
        # ('^(\s+ospf message-digest-key \d+ md5) .+', '\1 <secret hidden>'),
        # ('^(\s+ospf authentication-key) .+', '\1 <secret hidden>'),
        # ('^(\s+neighbor \S+ password) .+', '\1 <secret hidden>')
    ]
    GLOBAL_FILTER = [
        (r'Compiled on.*', r''),
        (r'.* up \d+ .*', r''),
        (r'Configuration last modified .*', r'')
    ]
    DEVICE_TYPE = "cisco_asa_ssh"

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
        cfg = self.netcon.send_command("show running-config")

        return self.filter(cfg)

    def get_metadata(self):
        results = dict()
        meta_cmds = ["show inventory", "show version"]
        for cmd in meta_cmds:
            results[cmd] = self.netcon.send_command(cmd)
        
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