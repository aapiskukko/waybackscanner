import sys
if sys.version_info[0] < 3:
    import urlparse
    from urllib import urlencode
    from urllib import unquote
else:
    import urllib.parse as urlparse
    from urllib.parse import urlencode
    from urllib.parse import unquote


class Url(object):
    def __init__(self, text=None):
        self.query = {}
        self.path = ""
        self.host = ""
        if text is not None:
            self._from_text(text)

    def _from_text(self, text):
        self._data = urlparse.urlparse(text)
        self.host = self._data.hostname
        self.scheme = self._data.scheme
        self.netloc = self._data.netloc
        self._data = list(self._data)
        self.query = urlparse.parse_qs(self._data[4], keep_blank_values=True)
        self.path = self._data[2]

    def __str__(self):
        try:
            self._data[4] = urlencode(self.query, doseq=True)
        except UnicodeEncodeError:
            print("Unicode error")
        text = urlparse.urlunparse(self._data)
        return unquote(text)

    @property
    def tld(self):
        host = self.host
        if "co.uk" in host:
            tld = host.split(".")[-3:]
        else:
            tld = host.split(".")[-2:]
        return ".".join(tld)
