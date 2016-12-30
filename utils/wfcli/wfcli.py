# coding=utf-8
import argparse
import logging
import os
import sys
import xmlrpc.client

logger = logging.getLogger('wfcli')


class WebFactionAPI():
    def __init__(self):
        super().__init__()
        self.server = xmlrpc.client.ServerProxy('https://api.webfaction.com/')
        self.session_id = self.account = None

    def connect(self, machine_name=""):
        if not self.session_id:
            logger.debug("Connecting to API server")
            username, password = os.environ['WEBFACTION_USER'], os.environ['WEBFACTION_PASS']
            api_version = 2
            self.session_id, self.account = self.server.login(username, password, machine_name,
                                                              api_version)

    def list_apps(self):
        self.connect()
        results = self.server.list_apps(self.session_id)
        return {a['name']: a for a in results}  # return apps keyed by id

    def create_app(self, app_name, app_type, autostart=False,
                   extra_info="", open_port=False):
        self.connect()
        app = self.server.create_app(self.session_id,
                                     app_name, app_type,
                                     autostart, extra_info, open_port
                                     )
        return app

    def create_domain(self, domain, subdomains=None):
        self.connect()
        if subdomains is None:
            subdomains = []

        domain = self.server.create_domain(self.session_id,
                                           domain,
                                           *subdomains,
                                           )
        return domain

    def list_domains(self):
        """ Return all domains. Domain is a key, so group by them """
        self.connect()
        results = self.server.list_domains(self.session_id)
        return {i['domain']: i['subdomains'] for i in results}

    def list_websites(self):
        """ Return all websites, name is not a key """
        self.connect()
        results = self.server.list_websites(self.session_id)

        return results

    def list_certificates(self):
        self.connect()
        results = self.server.list_certificates(self.session_id)

        return {i['name']: i for i in results}

    def list_ips(self):
        self.connect()
        return self.server.list_ips(self.session_id)

    def main_ip(self):
        ips = self.list_ips()
        return list(filter(lambda x: x['is_main'], ips))[0]['ip']  # one should be main

    def create_website(self, website_name, ip, enable_https, subdomains, certificate="", apps=()):
        self.connect()
        self.server.create_website(self.session_id,
                                   website_name, ip, enable_https, subdomains,
                                   certificate,
                                   *apps)

    def website_exists(self, website, websites=None):
        """ Look for websites matching the one passed """
        if websites is None:
            websites = self.list_websites()
        if isinstance(website, str):
            website = {"name": website}
        ignored_fields = ('id',)  # changes in these fields are ignored

        results = []
        for other in websites:
            different = False
            for key in website:
                if key in ignored_fields:
                    continue
                if other.get(key) != website.get(key):
                    different = True
                    break
            if different is False:
                results.append(other)
        return results


def get_cli_parser():
    VERSION = '0.1a'
    parser = argparse.ArgumentParser(
        "Webfaction Command Line Interface",
        description="A CLI wrapper to Webfaction APIs"
    )

    parser.add_argument("-v", "--version", action="version", version=VERSION)
    parser.add_argument('action', choices=[
        'install'
    ])
    parser.add_argument('name')
    parser.add_argument('--redis-password')
    parser.add_argument('--app-name')
    return parser


if __name__ == '__main__':
    command = 'install redis --app-name tambeta'
    parser = get_cli_parser()
    args = parser.parse_args(command.split())
    print(args)
    if args.action == "install":
        if args.name == 'redis':
            if not args.app_name:
                print("Install Redis requires app name")
                sys.exit(1)

        else:
            print("Unknown install %s" % args.name)
