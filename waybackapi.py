import json
import requests

import logger
import rejects


log = logger.new_sublogger("waybapi")


class WaybackApi:
    def __init__(self):
        self._cdx_url = "http://web.archive.org/cdx/search/cdx"

    def _create_query(self, domain, index=0, get_count=False):
        url = f"{self._cdx_url}?"
        url += f"&url={domain}/*"
        url += "&output=json"
        for mime in rejects.mimes:
            url += f"&filter=!mimetype:{mime}"
        url += "&filter=statuscode:200"
        url += "&collapse=urlkey"
        url += "&fl=timestamp,original"
        url += "&from=2018"
        if get_count:
            url += "&showNumPages=true"
        else:
            url += f"&page={index}"
        return url

    def get_page_count(self, domain):
        url = self._create_query(domain, get_count=True)
        try:
            headers = {"User-Agent": "curl/7.58.0"}
            ret = requests.get(url, headers=headers)
            return int(ret.text)
        except requests.exceptions.RequestException as err:
            log.error(f"error getting page count: {err}")
        except ValueError as err:
            log.error(f"error converting to int: {err}")

    def get_page(self, domain, index):
        url = self._create_query(domain, index=index)
        try:
            headers = {"User-Agent": "curl/7.58.0"}
            ret = requests.get(url, headers=headers)
            if ret.status_code != 200:
                log.warn(f"status code {ret.status_code} when getting page")
            return json.loads(ret.text)
        except requests.exceptions.RequestException as err:
            log.error(f"error getting page {index}: {err}")

    def get_file(self, filee, ts):
        url = f"http://web.archive.org/web/{ts}id_/{filee}"
        log.debug("downloading %s", url)
        try:
            headers = {"User-Agent": "curl/7.58.0"}
            ret = requests.get(url, headers=headers)
            return url, ret.text
        except (requests.exceptions.RequestException, MemoryError) as err:
            log.error(f"error getting file: {err}")
