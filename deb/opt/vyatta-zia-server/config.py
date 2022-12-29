#!/usr/bin/env python3
import os

from sys import exit

from vyos.config import Config
from vyos.configdict import dict_merge
from vyos.configverify import verify_vrf
from vyos.util import call
from vyos.template import render
from vyos import ConfigError
from vyos import airbag
from jinja2 import Template


airbag.enable()

config_file = r'/etc/default/zia-server'

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()
    base = ['service', 'zia-server']
    if not conf.exists(base):
        return None

    zia_server = conf.get_config_dict(base, get_first_key=True)

    return zia_server

def verify(zia_server):
    if zia_server is None:
        return None

    # upstream configuration is required for zia to work as expected
    if "upstream" not in zia_server:
        print("ZIA-Server upstream configuration is required!")
        exit(1)
        
    # upstream configuration requires address and port
    error = False
    if "address" not in zia_server["upstream"]:
        print("Missing ZIA-Server upstream address!")
        error = True
    if "port" not in zia_server["upstream"]:
        print("Missing ZIA-Server upstream port!")
        error = True
    if error:
        exit(1)

    verify_vrf(zia_server)
    return None

def generate(zia_server):
    if zia_server is None:
        if os.path.isfile(config_file):
            os.unlink(config_file)
        return None

    with open('/opt/vyatta-zia-server/config.j2', 'r') as tmpl, open(config_file, 'w') as out:
        template = Template(tmpl.read()).render(data=zia_server)
        out.write(template)

    # Reload systemd manager configuration
    call('systemctl daemon-reload')

    return None

def apply(zia_server):
    if zia_server is None:
        # zia_server is removed in the commit
        call('systemctl stop zia-server.service')
        return None

    call('systemctl restart zia-server.service')
    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
