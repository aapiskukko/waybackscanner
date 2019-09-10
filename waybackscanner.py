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
        self._found_kws = {}
        self._urls_file = None
        self._kws_file = None
        self._kw_cands = utils.import_keywords("lists/keywords.txt.1")

        try:
            os.mkdir("temp")
        except FileExistsError:
            pass

    def find(self, domain):
        url = Url(domain)
        name = url.host or url.path
        self._urls.clear()
        self._found_kws.clear()
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
        items = self._api.get_page(domain, index)
        for item in items[1:]:
            url = Url(item[0])
            if utils.allowed_url(url):
                wb_url, text = self._api.get_file(str(url), item[1])
                if not text:
                    continue
                self.find_urls(url, text)
                self.find_keywords_2(str(url), wb_url, text)

    def find_urls(self, url, text):
        with open(self._urls_file, "a") as fl:
            code = utils.url_exists(url)
            if str(url) not in self._urls and code:
                fl.write(f"{str(url)} {code}\n")
                self._urls.append(str(url))
                log.info(f"URL: {str(url)} {code}")

            parsed = utils.parse_urls(url, text)
            for item in parsed:
                code = utils.url_exists(url)
                if utils.allowed_url(Url(item)) and item not in self._urls and code:
                    self._urls.append(item)
                    log.info(f"URL: {item} {code}")
                    fl.write(f"{item} {code}\n")

    # def find_keywords(self, url, text):
        # for kw in utils.import_keywords("lists/keywords.txt"):
            # ptr = r"({}[a-zA-Z0-9_]*)\s*[=:]?\s*[\"\']{{1}}([a-zA-Z0-9-\:/.?#]{{2,}})[\"\']{{1}}".format(kw)
            # rex = re.compile(ptr, re.IGNORECASE)
            # matches = rex.findall(text)
            # if not matches:
                # continue
            # with open(self._kws_file, "a") as fl:
                # for match in matches:
                    # kw = f"{url} {match[0]}={match[1]}"
                    # if kw not in self._kws:
                        # log.info(f"KEYWORD: {kw}")
                        # fl.write(f"{kw}\n")
                        # self._kws.append(kw)

    def find_keywords_2(self, url, wb_url, text):
        text = text.replace(" ", "")
        matches = []
        for kw in self._kw_cands:
            if kw in text:
                matches.append(kw)
        if not matches:
            return
        with open(self._kws_file, "a") as fl:
            for match in matches:
                if not self._found_kws.get(url):
                    self._found_kws[url] = []
                if match not in self._found_kws[url]:
                    log.info(f"KEYWORD: {wb_url} {match}")
                    self._found_kws[url].append(match)
                    fl.write(f"{wb_url} {match}\n")


def main():
    logger.init(logging.INFO, None, True)
    wbscan = WaybackScanner()
    wbscan.find(sys.argv[1])


if __name__ == "__main__":
    main()
