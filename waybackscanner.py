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
import time
import hashlib

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
        self._found_files = set()

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
        log.info("getting page %s urls", index)
        items = self._api.get_page(domain, index)
        log.info("found %s urls in page %s", len(items), index)
        pool = Pool(1)
        for item in items[1:]:
            url = Url(item[0])
            if utils.allowed_url(url):
                pool.spawn(self.handle_file, str(url), item[1])

    def handle_file(self, url, ts):
        wb_url, text = self._api.get_file(url, ts)
        if text:
            md5sum = hashlib.md5(text.encode("utf-8")).hexdigest()
            if md5sum not in self._found_files:
                # self.find_urls(url, text)
                self.find_keywords(str(url), wb_url, text)
                self._found_files.add(md5sum)

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

    def find_keywords(self, url, wb_url, text):
        log.debug("finding keywords for %s", wb_url)
        kws = {
            "key",
            "token",
            "hash",
            "password",
            "salasana",
            "username",
            "secret",
            "login"}

        text = text.replace(" ", "")
        for kw in kws:
            ptr = r"(([a-z0-9]{{1,12}}[-_]?){{1,3}}{})[=:]{{1}}[\"\']{{1}}([a-z0-9_-]{{2,512}})[\"\']{{1}}".format(kw)
            rex = re.compile(ptr, re.IGNORECASE)
            now = time.time()
            matches = rex.findall(text)
            log.debug("regex delay %s s", round(time.time() - now, 3))
            for match in matches:
                log.info(f"KEYWORD: {url} {match[0]}={match[2]}")
            if not matches:
                continue
            with open(self._kws_file, "a") as fl:
                for match in matches:
                    log.info(f"KEYWORD: {wb_url} {match[0]}={match[2]}")
                    fl.write(f"{wb_url} {match[0]}={match[2]}\n")


    # def find_keywords_2(self, url, wb_url, text):
        # text = text.replace(" ", "")
        # matches = []
        # for kw in self._kw_cands:
            # if kw in text:
                # matches.append(kw)
        # if not matches:
            # return
        # with open(self._kws_file, "a") as fl:
            # for match in matches:
                # if not self._found_kws.get(url):
                    # self._found_kws[url] = []
                # if match not in self._found_kws[url]:
                    # log.info(f"KEYWORD: {wb_url} {match}")
                    # self._found_kws[url].append(match)
                    # fl.write(f"{wb_url} {match}\n")


def main():
    logger.init(logging.INFO, None, True)
    wbscan = WaybackScanner()
    wbscan.find(sys.argv[1])


if __name__ == "__main__":
    main()
