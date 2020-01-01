import gevent.monkey
import gevent
gevent.monkey.patch_all()
from gevent.pool import Pool
import sys
import logging
import os
import hashlib
import time

import logger
import utils
from url import Url
from waybackapi import WaybackApi
from apikeyfinder import ApiKeyFinder


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
        self._urls_file = f"temp/{name}-urls.txt"
        self._kws_file = f"temp/{name}-keys.txt"
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
        log.debug("getting page %s urls", index)
        items = self._api.get_page(domain, index)
        if items:
            log.info("found %s urls in page %s", len(items), index)
            pool = Pool(1)
            for item in items[1:]:
                url = Url(item[0])
                if utils.allowed_url(url):
                    pool.spawn(self.handle_file, url, item[1])

    def handle_file(self, url, ts):
        wb_url, text = self._api.get_file(url, ts)
        if text:
            md5sum = hashlib.md5(text.encode("utf-8")).hexdigest()
            if md5sum not in self._found_files:
                self.find_urls(url, text)
                self.find_keywords(wb_url, text)
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

    def find_keywords(self, wb_url, text):
        log.debug("finding keywords for %s", wb_url)
        keyfinder = ApiKeyFinder()
        now = time.time()
        keys = keyfinder.find(text)
        log.debug("found {} keys in {} s".format(len(keys), round(time.time() - now, 3)))
        with open(self._kws_file, "a") as fl:
            for key in keys:
                log.info(f"KEYWORD: {wb_url} {key.key}={key.value}")
                fl.write(f"{wb_url} {key.key}={key.value}\n")

def main():
    logger.init(logging.DEBUG, None, True)
    wbscan = WaybackScanner()
    wbscan.find(sys.argv[1])


if __name__ == "__main__":
    main()
