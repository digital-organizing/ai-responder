import csv
import os
import urllib.parse
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import w3lib.url


def _load_parameters():
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))

    with open(dir_path / "data/params.csv", "r") as fp:
        reader = csv.reader(fp)
        for row in reader:
            yield row[0]


REMOVE_URL_PARAMETERS = list(_load_parameters())


def sanitize_url(url: str, base_url: str = "") -> ParseResult:
    url = urllib.parse.urljoin(base_url, url)

    url = w3lib.url.canonicalize_url(url)
    url = w3lib.url.url_query_cleaner(url, REMOVE_URL_PARAMETERS, remove=True)

    parsed_url = urlparse(url)

    if parsed_url.scheme not in ["http", "https"]:
        raise ValueError("Invalid scheme for url %s: %s" % (url, parsed_url.scheme))

    return parsed_url._replace(scheme="https")
