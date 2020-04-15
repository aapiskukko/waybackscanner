#!/usr/bin/python

import os
import signal
import logging

from configparser import SafeConfigParser
from configparser import DuplicateSectionError
import logger

log = logger.new_sublogger("conf")


class ConfigReader(object):
    def __init__(self):
        self.log_level = logging.DEBUG
        self.log_file = "app.log"
        self.log_stdout = True
        self.conf_file = "conf/default.conf"
        self.target_host = ""
        self.keys_only = False
        self.only_params = True

        signal.signal(signal.SIGHUP, self.sighup_handler)

    def read(self, conf_file=None):
        if conf_file is not None:
            self.conf_file = conf_file

        if not self.conf_file or not os.path.exists(self.conf_file):
            raise ConfigReaderException("no configuration file found in path %s" % self.conf_file)
        confparser = SafeConfigParser()
        confparser.read(self.conf_file)
        self.apply(confparser)
        return True

    def apply(self, confparser):
        if "log" in confparser.sections():
            for key, val in confparser.items("log"):
                if key == "file":
                    self.log_file = val
                if key == "level":
                    self.log_level = val
                if key == "stdout":
                    self.log_stdout = val.lower() == "true"

        if "target" in confparser.sections():
            for key, val in confparser.items("target"):
                if key == "host":
                    self.target_host = val
                if key == "keywords-only":
                    self.keys_only = val.lower() == "true"
                if key == "query-parameter-urls-only":
                    self.only_params = val.lower() == "true"

    def show(self):
        log.info("---=== CONFIG %s ===---", self.conf_file)
        log.info("log")
        log.info("|-level: %s", self.log_level)
        log.info("|-file: %s", self.log_file)
        log.info("|-stdout: %s", self.log_stdout)
        log.info("target")
        log.info("|-host: %s", self.target_host)
        log.info("|-keywords-only: %s", self.keys_only)
        log.info("|-query-parameter-urls-only: %s", self.only_params)
        log.info("---=== CONFIG %s ===---", self.conf_file)

    def override(self, args):
        if args.conf_file:
            self.conf_file = args.conf_file
        if args.parameter:
            self.override_generic(args.parameter)

    def override_generic(self, params):
        cp = SafeConfigParser()
        try:
            for param in params:
                sec, param = param.split(".", 1)
                key, val = param.split("=")
                try:
                    cp.add_section(sec)
                except DuplicateSectionError:
                    pass
                cp.set(sec, key, val)
        except ValueError:
            raise ConfigReaderException("invalid \"config\" argument syntax: %s" % param)
        self.apply(cp)

    def sighup_handler(self, signum, frame):
        log.info("reloading config file in path %s", self.conf_file)
        self.read(self.conf_file)
        self.show()


class ConfigReaderException(Exception):
    pass
