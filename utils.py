import re
import linkfinder
import urllib.parse as urlparse
import requests

import rejects


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


def import_keywords(path):
    out = []
    with open(path, "r+") as keywords:
        for kw in keywords:
            if not kw.startswith("#"):
                kw = kw.strip()
                out.append(kw.lower())
    return out


def is_hash(val):
    rex = "(i^[0-9a-fA-F_.-]{4,})$"
    return re.match(rex, val)

def url_exists(url, ignore_codes, ignore_texts, redir=False):
    try:
        ret = requests.get(url, allow_redirects=redir, timeout=2)
        if ret.status_code not in ignore_codes:
            if all(text not in ret.text for text in ignore_texts):
                return ret.status_code
        return False
    except requests.RequestException:
        return False

def allowed_url(url):
    for suffix in rejects.suffixes:
        if suffix.lower() in url.path.lower():
            return False
    for domain in rejects.domains:
        if domain.lower() in url.host:
            return False
    for kw in rejects.keywords:
        if kw.lower() in str(url).lower():
            return False
    return True

def has_query_params(url):
    return "?" in url
