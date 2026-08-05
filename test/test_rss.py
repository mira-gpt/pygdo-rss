import os
import unittest
from unittest.mock import patch

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.rss.GDO_RSSAbbo import GDO_RSSAbbo
from gdo.rss.GDO_RSSEntry import GDO_RSSEntry
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed
from gdo.rss.RSSParser import RSSParser
from gdo.rss.module_rss import module_rss
from gdotest.TestUtil import cli_plug, reinstall_module, cli_gizmore, GDOTestCase, WebPlug, install_module


class module_rss_Test(GDOTestCase):

    async def asyncSetUp(self):
        await super().asyncSetUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        install_module('rss')
        loader.load_modules_db(True)
        WebPlug.COOKIES = {}
        Application.init_cli()
        loader.init_modules(True, True)
        loader.init_cli()

    def test_00_reinstall(self):
        reinstall_module('rss')
        self.assertIs(type(module_rss.instance()), module_rss, "Cannot re-install module rss.")

    def test_01_add_cli(self):
        giz = cli_gizmore()
        out = cli_plug(giz, '$rss.add hackernews https://news.ycombinator.com/rss')
        self.assertIn('RSS feed hackernews has been added.', out, 'RSS feed was not created.')
        feed = GDO_RSSFeed.table().get_by_vals({'rss_name': 'hackernews'})
        self.assertIsNone(feed.gdo_val('rss_last_check'), 'New feeds must not be checked before the timer runs.')

    def test_02_abbo_cli(self):
        giz = cli_gizmore()
        out = cli_plug(giz, '$rss.abbo hackernews')
        self.assertIn('RSS feed hackernews has been subscribed.', out, 'RSS feed was not subscribed.')
        feed = GDO_RSSFeed.table().get_by_vals({'rss_name': 'hackernews'})
        channel = giz.get_server().get_or_create_channel('test_channel')
        abbo = GDO_RSSAbbo.table().get_by_vals({
            'rsa_feed': feed.get_id(),
            'rsa_channel': channel.get_id(),
        })
        self.assertIsNotNone(abbo, 'Channel RSS subscription was not created.')

    def test_03_check_feed(self):
        feed = GDO_RSSFeed.table().get_by_vals({'rss_name': 'hackernews'})
        response = type('Response', (), {'status': 200})()
        content = b'''<?xml version="1.0"?><rss version="2.0"><channel><item>
            <title>Timer entry</title><link>https://news.ycombinator.com/item?id=42</link>
            <guid>hn-42</guid><pubDate>Tue, 05 Aug 2026 16:00:00 +0000</pubDate>
            </item></channel></rss>'''
        with patch.object(GDO_RSSFeed, '_load_feed', return_value=(response, content)):
            self.assertEqual(1, Application.LOOP.run_until_complete(feed.check_feed()))
            self.assertEqual(0, Application.LOOP.run_until_complete(feed.check_feed()))
        self.assertIsNotNone(feed.gdo_val('rss_last_check'), 'Feed check time was not recorded.')
        self.assertIsNotNone(GDO_RSSEntry.table().get_by_vals({
            'rse_feed': feed.get_id(),
            'rse_uid': 'hn-42',
        }), 'Fetched RSS entry was not stored.')

    def test_04_parse_rss(self):
        entries = RSSParser.parse('''<?xml version="1.0"?>
            <rss version="2.0"><channel><item>
            <title>Hacker News</title><link>https://news.ycombinator.com/item?id=1</link>
            <guid>hn-1</guid><pubDate>Tue, 05 Aug 2026 16:00:00 +0000</pubDate>
            </item></channel></rss>''')
        self.assertEqual(1, len(entries))
        self.assertEqual('hn-1', entries[0].uid)
        self.assertEqual('Hacker News', entries[0].title)
        self.assertEqual('https://news.ycombinator.com/item?id=1', entries[0].url)
        self.assertEqual(2026, entries[0].published.year)

    def test_05_parse_atom(self):
        entries = RSSParser.parse('''<?xml version="1.0"?>
            <feed xmlns="http://www.w3.org/2005/Atom"><entry>
            <id>tag:example.org,2026:1</id><title>Atom news</title>
            <link href="https://example.org/news/1"/><updated>2026-08-05T16:00:00Z</updated>
            </entry></feed>''')
        self.assertEqual(1, len(entries))
        self.assertEqual('tag:example.org,2026:1', entries[0].uid)
        self.assertEqual('Atom news', entries[0].title)
        self.assertEqual('https://example.org/news/1', entries[0].url)
        self.assertEqual(2026, entries[0].published.year)

if __name__ == '__main__':
    unittest.main()
