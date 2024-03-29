import gevent.monkey
import gevent
gevent.monkey.patch_all()
from gevent.pool import Pool
import sys
import os
import hashlib
import time

import logger
import utils
from url import Url
from waybackapi import WaybackApi
from apikeyfinder import ApiKeyFinder
from configreader import ConfigReader, ConfigReaderException
from argsreader import ArgsReader, ArgsReaderException


log = logger.new_sublogger("waybscan")

class WaybackScanner:
    def __init__(self, conf):
        self._conf = conf
        self._api = WaybackApi()
        self._urls = []
        self._found_kws = set()
        self._urls_file = None
        self._kws_file = None
        self._found_files = set()
        self._since = self._conf.start_year

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

        count = self._api.get_page_count(domain, since=self._since)
        log.info(f"requesting {count} pages")

        pool = Pool(min(8, count))
        for i in range(count):
            pool.spawn(self.handle_page, domain, i)
        pool.join()
        return self._urls

    def handle_page(self, domain, index):
        log.debug("getting page %s urls", index)
        items = self._api.get_page(domain, index, since=self._since)
        if items:
            log.info("found %s urls in page %s", len(items), index)
            pool = Pool(1)
            for item in items[1:]:
                url = Url(item[1])
                if utils.allowed_url(url):
                    pool.spawn(self.handle_file, url, item[0])

    def handle_file(self, url, ts):
        wb_url, text = self._api.get_file(url, ts)
        if text:
            md5sum = hashlib.md5(text.encode("utf-8")).hexdigest()
            if md5sum not in self._found_files:
                if not self._conf.keys_only:
                    self.find_urls(url, text)
                self.find_keywords(wb_url, text)
                self._found_files.add(md5sum)

    def find_urls(self, url, text):
        with open(self._urls_file, "a") as fl:
            if str(url) not in self._urls:
                if self._conf.only_params:
                    if utils.has_query_params(str(url)):
                        fl.write(f"{str(url)}\n")
                        self._urls.append(str(url))
                        log.info(f"URL: {str(url)}")
                else:
                    fl.write(f"{str(url)}\n")
                    self._urls.append(str(url))
                    log.info(f"URL: {str(url)}")

            parsed = utils.parse_urls(url, text)
            for item in parsed:
                if utils.allowed_url(Url(item)) and item not in self._urls:
                    if self._conf.only_params:
                        if utils.has_query_params(item):
                            self._urls.append(item)
                            log.info(f"URL: {item}")
                            fl.write(f"{item}\n")
                    else:
                        self._urls.append(item)
                        log.info(f"URL: {item}")
                        fl.write(f"{item}\n")

    def find_keywords(self, wb_url, text):
        log.debug("finding keywords for %s", wb_url)
        keyfinder = ApiKeyFinder()
        now = time.time()
        keys = keyfinder.find(text)
        log.debug("found {} keys in {} s".format(len(keys), round(time.time() - now, 3)))
        with open(self._kws_file, "a") as fl:
            for key in keys:
                if key not in self._found_kws:
                    log.info(f"KEYWORD: {wb_url} {key.key}={key.value}")
                    fl.write(f"{wb_url} {key.key}={key.value}\n")
                    self._found_kws.add(key)

def main():
    conf = ConfigReader()
    args = ArgsReader()

    try:
        args.read()
        conf.read(args.conf_file)
        conf.override(args)
        logger.init(conf.log_level, conf.log_file, conf.log_stdout)
        conf.show()
    except (ArgsReaderException, ConfigReaderException) as err:
        print(f"error in init: {err}")
        sys.exit(1)

    wbscan = WaybackScanner(conf)
    try:
        wbscan.find(conf.target_host)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
