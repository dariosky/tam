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

    def connect(self):
        if not self.session_id:
            logger.debug("Connecting to API server")
            username, password = os.environ['WEBFACTION_USER'], os.environ['WEBFACTION_PASS']
            self.session_id, self.account = self.server.login(username, password)

    def list_apps(self):
        self.connect()
        return self.server.list_apps(self.session_id)

    def create_app(self, app_name, app_type):
        self.connect()
        app = self.server.create_app(self.session_id,
                                     app_name,
                                     app_type,
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
