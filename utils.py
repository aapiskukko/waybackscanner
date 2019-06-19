import re
import linkfinder
import sys

if sys.version_info[0] < 3:
    import urlparse
else:
    import urllib.parse as urlparse


def parse_absolute_urls(text):
    rex = r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
    urls = re.findall(rex, text)
    out = []
    for url in urls:
        if len(url) > 1:
            scheme = url[0] + "://"
            out.append(scheme + ''.join(url[1:]))
        else:
            out.append(url)
    return out


def parse_urls(url, text):
    out = []
    index = url.path.rfind("/")
    path = url.path[:index + 1]
    base = url.scheme + "://" + url.netloc + path
    relatives = linkfinder.parser_file(text, linkfinder.regex_str, mode=0)
    for item in relatives:
        out.append(urlparse.urljoin(base, item["link"]))
    return out


def parse_tld(url):
    host = urlparse.urlparse(url).hostname
    if "co.uk" in host:
        tld = host.split(".")[-3:]
    else:
        tld = host.split(".")[-2:]
    return ".".join(tld)


def parse_params(url):
    url = urlparse.urlparse(url)
    return urlparse.parse_qsl(url.query)


def import_keywords():
    out = []
    with open("lists/keywords.txt", "r+") as keywords:
        for kw in keywords:
            if not kw.startswith("#"):
                kw = kw.strip()
                out.append(kw.lower())
    return out


def is_hash(val):
    rex = "(i^[0-9a-fA-F_.-]{4,})$"
    return re.match(rex, val)
