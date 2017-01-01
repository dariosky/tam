#!/usr/bin/env python
# coding=utf-8
import argparse
import logging
import sys

from tossl import WebfactionWebsiteToSsl

logger = logging.getLogger('wfcli')


def get_cli_parser():
    VERSION = '0.1a'
    parser = argparse.ArgumentParser(
        "Webfaction Command Line Interface",
        description="A CLI wrapper to Webfaction APIs"
    )

    parser.add_argument("-v", "--version", action="version", version=VERSION)
    parser.add_argument('action', choices=[
        'install', 'secure'
    ])
    parser.add_argument('name')
    parser.add_argument('--redis-password')
    parser.add_argument('--app-name')
    parser.add_argument('--webfaction-host')
    return parser


if __name__ == '__main__':
    # example './wfcli.py install redis --app-name tambeta'
    parser = get_cli_parser()
    args = parser.parse_args()
    if args.action == "install":
        if args.name == 'redis':
            if not args.app_name:
                print("Install Redis requires app name")
                sys.exit(1)
        else:
            print("Unknown install %s" % args.name)
    elif args.action == "secure":
        print("Converting websites in the domain %s to HTTPS" % args.name)
        w = WebfactionWebsiteToSsl(
            webfaction_host=args.webfaction_host,
        )
        w.secure(domain=args.name)
