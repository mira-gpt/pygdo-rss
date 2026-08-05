from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree


@dataclass(frozen=True)
class RSSParsedEntry:
    uid: str
    title: str
    url: str | None
    published: datetime | None


class RSSParser:
    """Parse RSS 2.0 and Atom XML without fetching remote resources."""

    @staticmethod
    def parse(xml: str | bytes) -> list[RSSParsedEntry]:
        root = ElementTree.fromstring(xml)
        root_name = RSSParser._name(root.tag)
        if root_name == 'rss':
            channel = RSSParser._child(root, 'channel')
            return [] if channel is None else RSSParser._rss_entries(channel)
        if root_name == 'feed':
            return RSSParser._atom_entries(root)
        raise ValueError(f'Unsupported feed root: {root_name}')

    @staticmethod
    def _rss_entries(channel: ElementTree.Element) -> list[RSSParsedEntry]:
        entries = []
        for item in RSSParser._children(channel, 'item'):
            url = RSSParser._text(item, 'link')
            uid = RSSParser._text(item, 'guid') or url
            if uid:
                entries.append(RSSParsedEntry(
                    uid=uid,
                    title=RSSParser._text(item, 'title') or '',
                    url=url,
                    published=RSSParser._date(RSSParser._text(item, 'pubDate')),
                ))
        return entries

    @staticmethod
    def _atom_entries(feed: ElementTree.Element) -> list[RSSParsedEntry]:
        entries = []
        for item in RSSParser._children(feed, 'entry'):
            url = RSSParser._atom_url(item)
            uid = RSSParser._text(item, 'id') or url
            if uid:
                entries.append(RSSParsedEntry(
                    uid=uid,
                    title=RSSParser._text(item, 'title') or '',
                    url=url,
                    published=RSSParser._date(RSSParser._text(item, 'published') or RSSParser._text(item, 'updated')),
                ))
        return entries

    @staticmethod
    def _atom_url(item: ElementTree.Element) -> str | None:
        links = RSSParser._children(item, 'link')
        link = next((link for link in links if link.get('rel', 'alternate') == 'alternate'), links[0] if links else None)
        return link.get('href') if link is not None else None

    @staticmethod
    def _date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                return parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None

    @staticmethod
    def _name(tag: str) -> str:
        return tag.rsplit('}', 1)[-1]

    @staticmethod
    def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
        return [child for child in element if RSSParser._name(child.tag) == name]

    @staticmethod
    def _child(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
        return next(iter(RSSParser._children(element, name)), None)

    @staticmethod
    def _text(element: ElementTree.Element, name: str) -> str | None:
        child = RSSParser._child(element, name)
        return child.text.strip() if child is not None and child.text else None
