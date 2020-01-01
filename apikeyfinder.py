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

class ApiKeyFinder:
    def __init__(self):
        self._results = []
        self._pool = Pool(min(10, len(KEYWORDS)))
        self._template = self._format_pattern()

    def _format_pattern(self):
        # match MY_API_{KEYWORD} style pattern
        ptr = r"(([a-z0-9]{{1,12}}[-_]?){{1,5}}{})"
        # match variable assignment char = or :
        ptr += r"[=:]{{1}}"
        # match string begin char " or ' or `
        ptr += r"[\"\'`]{{1}}"
        # match api key content
        ptr += r"([a-z0-9_-]{{2,512}})"
        # match string begin char " or ' or `
        ptr += r"[\"\'`]{{1}}"
        return ptr

    def find(self, text):
        self._results.clear()
        text = text.replace(" ", "")
        for keyword in KEYWORDS:
            self._pool.spawn(self._handle, text, keyword)
        self._pool.join()
        return self._results

    def _handle(self, text, keyword):
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
    for key in keys:
        print("found {}={}".format(key.key, key.value))
    print("found {} keys in {} s".format(len(keys), round(time.time() - now, 3)))


if __name__ == "__main__":
    main()
