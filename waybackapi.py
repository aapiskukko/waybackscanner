import json
import requests

import logger
import rejects


log = logger.new_sublogger("waybapi")


class WaybackApi:
    def __init__(self):
        self._cdx_url = "http://web.archive.org/cdx/search/cdx"

    def get_page_count(self, domain):
        url = f"{self._cdx_url}?"
        url += f"&url={domain}/*"
        url += "&showNumPages=true"

        try:
            ret = requests.get(url)
            return int(ret.text)
        except requests.exceptions.RequestException as err:
            log.error(f"error getting page count: {err}")
        except ValueError as err:
            log.error(f"error converting to int: {err}")

    def get_page(self, domain, index):
        url = f"{self._cdx_url}?"
        url += f"&url={domain}/*"
        url += "&output=json"
        for mime in rejects.mimes:
            url += f"&filter=!mimetype:{mime}"
        url += "&collapse=digest"
        url += "&fl=original,timestamp,statuscode,length"
        url += f"&page={index}"

        try:
            ret = requests.get(url)
            if ret.status_code != 200:
                log.warn(f"status code {ret.status_code} when getting page")
            return json.loads(ret.text)
        except requests.exceptions.RequestException as err:
            log.error(f"error getting page {index}: {err}")

    def get_file(self, filee, ts):
        url = f"http://web.archive.org/web/{ts}id_/{filee}"
        log.debug("downloading %s", url)
        try:
            ret = requests.get(url)
            return url, ret.text
        except (requests.exceptions.RequestException, MemoryError) as err:
            log.error(f"error getting file: {err}")
