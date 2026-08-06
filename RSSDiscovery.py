from html.parser import HTMLParser
from urllib.parse import urljoin


class _FeedLinkParser(HTMLParser):

    FEED_TYPES = {
        'application/atom+xml',
        'application/rss+xml',
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag.lower() != 'link':
            return
        attributes = {key.lower(): value for key, value in attrs}
        rel = (attributes.get('rel') or '').lower().split()
        content_type = (attributes.get('type') or '').split(';', 1)[0].strip().lower()
        href = attributes.get('href')
        if 'alternate' in rel and content_type in self.FEED_TYPES and href:
            self.urls.append(href)


class RSSDiscovery:
    """Discover RSS and Atom alternate links in a website document."""

    @classmethod
    def discover(cls, html: str | bytes, page_url: str) -> list[str]:
        if isinstance(html, bytes):
            html = html.decode('utf-8', errors='replace')
        parser = _FeedLinkParser()
        parser.feed(html)
        return list(dict.fromkeys(urljoin(page_url, href) for href in parser.urls))
