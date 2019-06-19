import gevent.monkey
import gevent
gevent.monkey.patch_all()
from gevent.pool import Pool
import requests
import sys
import logging
import json
import os
import re

import logger
import utils
import rejects
from url import Url
from waybackapi import WaybackApi


log = logger.new_sublogger("waybscan")


class WaybackScanner:
    def __init__(self):
        self._api = WaybackApi()
        self._urls = []
        self._kws = []
        self._urls_file = None

        try:
            os.mkdir("temp")
        except FileExistsError:
            pass

    def find(self, domain):
        url = Url(domain)
        name = url.host or url.path
        self._urls.clear()
        self._kws.clear()
        self._urls_file = f"temp/{name}-wburls.txt"
        self._kws_file = f"temp/{name}-keywords.txt"
        try:
            os.remove(self._urls_file)
            os.remove(self._kws_file)
        except OSError:
            pass

        count = self._api.get_page_count(domain)
        log.info(f"requesting {count} pages")

        pool = Pool(min(8, count))
        for i in range(count):
            pool.spawn(self.handle_page, domain, i)
        pool.join()
        return self._urls

    def handle_page(self, domain, index):
        for mime in rejects.mimes:
            items = self._api.get_page(domain, index, mime)
            for item in items[1:]:
                url = Url(item[0])
                if self.allowed_url(url):
                    wb_url, text = self._api.get_file(str(url), item[1])
                    if not text:
                        continue
                    self.find_urls(url, text)
                    self.find_keywords(wb_url, text)

    def find_urls(self, url, text):
        with open(self._urls_file, "a") as f:
            if str(url) not in self._urls:
                f.write(f"{str(url)}\n")
                self._urls.append(str(url))
                log.info(f"URL: {str(url)}")

            parsed = utils.parse_urls(url, text)
            for item in parsed:
                if self.allowed_url(Url(item)) and item not in self._urls:
                    self._urls.append(item)
                    log.info(f"URL: {item}")
                    f.write(f"{item}\n")

    def allowed_url(self, url):
        for suffix in rejects.suffixes:
            if suffix in url.path:
                return False
        for domain in rejects.domains:
            if domain in url.host:
                return False
        for kw in rejects.keywords:
            if kw in url.path:
                return False
        return True

    def find_keywords(self, url, text):
        for kw in utils.import_keywords():
            ptr = r"({}[a-zA-Z0-9_]*)\s*[=:]?\s*[\"\']{{1}}([a-zA-Z0-9-\:/.?#]+)[\"\']{{1}}".format(kw)
            rex = re.compile(ptr, re.IGNORECASE)
            matches = rex.findall(text)
            if not matches:
                continue
            with open(self._kws_file, "a") as f:
                for match in matches:
                    kw = f"{url} {match[0]}={match[1]}"
                    if kw not in self._kws:
                        log.info(f"KEYWORD: {kw}")
                        f.write(f"{kw}\n")
                        self._kws.append(kw)


def main():
    logger.init(logging.INFO, None, True)
    wbscan = WaybackScanner()
    wbscan.find(sys.argv[1])


if __name__ == "__main__":
    main()
