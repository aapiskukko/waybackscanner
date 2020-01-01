import gevent.monkey
gevent.monkey.patch_all()
import gevent
from gevent.pool import Pool
import sys
import re
import time
import collections


KEYWORDS = {
    "key",
    "token",
    "hash",
    "password",
    "salasana",
    "username",
    "secret",
    "login"}

ApiKey = collections.namedtuple('ApiKey', 'key value')
PreFilterMatch = collections.namedtuple('PreFilterMatch', 'key text')

class ApiKeyFinder:
    """ Find API keys from Javascript content """
    def __init__(self):
        self._results = []
        self._pool = Pool(min(10, len(KEYWORDS)))
        self._template = self._format_pattern()

    def _format_pattern(self):
        # match MY_API_{KEYWORD} pattern
        ptr = r"(([a-z0-9]{{1,12}}[-_]?){{1,3}}{})"
        # match variable assignment char = or :
        ptr += r"[=:]{{1}}"
        # match string begin char " or ' or `
        ptr += r"[\"\'`]{{1}}"
        # match api key content
        ptr += r"([a-z0-9_/+-]{{2,256}})"
        # match string begin char " or ' or `
        ptr += r"[\"\'`]{{1}}"
        return ptr

    def _pre_filter(self, text):
        text = text.replace("\r", "")
        text = text.replace("\n", "")
        text = text.replace(" ", "")
        template = r"{}[=:]{{1}}"
        offset_low = 100
        offset_high = 300
        out = []
        for keyword in KEYWORDS:
            try:
                pattern = template.format(keyword)
                rex = re.compile(pattern, re.IGNORECASE)
                res = rex.finditer(text)
                indices = [m.start() for m in res]
                for index in indices:
                    low = max(0, index - offset_low)
                    high = min(len(text), index + offset_high)
                    subst = text[low:high]
                    out.append(PreFilterMatch(keyword, subst))
            except ValueError:
                continue
        return out

    def find(self, text):
        self._results.clear()
        cands = self._pre_filter(text)
        for cand in cands:
            self._pool.spawn(self._handle, cand.key, cand.text)
        self._pool.join()
        return self._results

    def _handle(self, keyword, text):
        pattern = self._template.format(keyword)
        rex = re.compile(pattern, re.IGNORECASE)
        matches = rex.findall(text)
        for match in matches:
            key = match[0]
            val = match[2]
            item = ApiKey(key, val)
            if item not in self._results:
                self._results.append(item)

def main():
    key_finder = ApiKeyFinder()
    text = open(sys.argv[1]).read()
    now = time.time()
    keys = key_finder.find(text)
    if keys:
        for key in keys:
            print("found {}={}".format(key.key, key.value))
        print("found {} keys in {} s".format(len(keys), round(time.time() - now, 3)))


if __name__ == "__main__":
    main()
