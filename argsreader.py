#!/usr/bin/python

import argparse


class ArgsReader(object):

    def __init__(self):
        self.conf_file = None
        self.parameter = None

    def read(self):
        parser = argparse.ArgumentParser(description="Wayback Scanner")
        parser.add_argument(
            "-c", "--config", default=None, help="config file path")
        parser.add_argument(
            "-p", "--parameter", default=None, action="append",
            help="override parameter in config file")
        args = parser.parse_args()

        self.conf_file = args.config
        self.parameter = args.parameter


class ArgsReaderException(Exception):
    pass
