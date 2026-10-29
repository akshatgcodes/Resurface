import pytest

from app import fetch


@pytest.mark.parametrize("html,title,author", [
    ("<html><head><title> Deep   Work &amp; Focus </title></head>", "Deep Work & Focus", None),
    ('<meta property="og:title" content="OG Title"><title>Plain</title>', "OG Title", None),
    ('<meta content="Reversed" property="og:title">', "Reversed", None),
    ('<title>T</title><meta name="author" content="Cal Newport">', "T", "Cal Newport"),
    ("<p>no title</p>", None, None),
])
def test_parse_meta(html, title, author):
    assert fetch.parse_meta(html) == (title, author)


@pytest.mark.parametrize("url", [
    "http://localhost:6379/",
    "http://127.0.0.1/",
    "http://10.0.0.5/admin",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/",
    "file:///etc/passwd",
    "ftp://example.com/x",
])
def test_blocks_private_and_non_http(url):
    with pytest.raises(fetch.FetchError):
        fetch._check_public(url)
