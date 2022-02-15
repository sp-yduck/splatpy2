from urllib.parse import urlparse, parse_qs


def qsd_from_url(url):
    u = urlparse(url)
    querys_dict = parse_qs(u.query)
    return querys_dict


def qsd_from_url_fragment(url):
    u = urlparse(url)
    querys_dict = parse_qs(u.fragment)
    return querys_dict