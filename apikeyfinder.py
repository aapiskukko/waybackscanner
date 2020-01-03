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

# match keyword plus assignment operator
PRE_TEMPL = r"{}[=:]{{1}}"

# match MY_API_{KEYWORD} pattern
TEMPL = r"(([a-z0-9]{{1,12}}[-_]?){{1,3}}{})"
# match variable assignment char = or :
TEMPL += r"[=:]{{1}}"
# match string begin char " or ' or `
TEMPL += r"[\"\'`]{{1}}"
# match api key content
TEMPL += r"([a-z0-9_/+-]{{2,256}})"
# match string begin char " or ' or `
TEMPL += r"[\"\'`]{{1}}"

ApiKey = collections.namedtuple('ApiKey', 'key value')

class ApiKeyFinder:
    """ Find API keys from Javascript content """
    def __init__(self):
        self._results = []
        self._template = TEMPL
        self._pre_filters = self._build_filters(PRE_TEMPL)
        self._filters = self._build_filters(TEMPL)

    def _build_filters(self, templ):
        out = {}
        for keyword in KEYWORDS:
            pattern = templ.format(keyword)
            out[keyword] = re.compile(pattern, re.IGNORECASE)
        return out

    def _pre_filter(self, text):
        text = text.replace("\r", "")
        text = text.replace("\n", "")
        text = text.replace(" ", "")
        offset_low = 100
        offset_high = 300
        out = []
        for keyword, filt in self._pre_filters.items():
            try:
                res = filt.finditer(text)
                indices = [m.start() for m in res]
                for index in indices:
                    low = max(0, index - offset_low)
                    high = min(len(text), index + offset_high)
                    sub_text = text[low:high]
                    out.append((keyword, sub_text))
            except ValueError:
                continue
        return out

    def find(self, text):
        self._results.clear()
        cands = self._pre_filter(text)
        for keyword, sub_text in cands:
            matches = self._filters[keyword].findall(sub_text)
            for match in matches:
                key = match[0]
                val = match[2]
                item = ApiKey(key, val)
                if item not in self._results:
                    self._results.append(item)
        return self._results

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
