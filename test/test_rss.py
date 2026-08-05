import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Render import Mode, Render
from gdo.date.Time import Time
from gdo.rss.GDO_RSSAbbo import GDO_RSSAbbo
from gdo.rss.GDO_RSSEntry import GDO_RSSEntry
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed
from gdo.rss.RSSParser import RSSParsedEntry, RSSParser
from gdo.rss.method.abbo import abbo
from gdo.rss.method.news import news
from gdo.rss.module_rss import module_rss
from gdo.table.GDT_Table import TableMode
from gdotest.TestUtil import cli_plug, reinstall_module, cli_gizmore, cli_user, GDOTestCase, WebPlug, install_module


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
        entry = RSSParsedEntry('hn-add', 'Initial entry', 'https://news.ycombinator.com/item?id=1', datetime.now(timezone.utc))
        with patch.object(GDO_RSSFeed, 'load_entries', new=AsyncMock(return_value=[entry])):
            out = cli_plug(giz, '$rss.add hackernews https://news.ycombinator.com/rss')
        self.assertIn('RSS feed hackernews has been added.', out, 'RSS feed was not created.')
        feed = GDO_RSSFeed.table().get_by_vals({'rss_name': 'hackernews'})
        self.assertIsNotNone(feed.gdo_val('rss_last_check'), 'Initial feed check was not recorded.')
        self.assertIsNotNone(GDO_RSSEntry.table().get_by_vals({
            'rse_feed': feed.get_id(),
            'rse_uid': 'hn-add',
        }), 'Initial RSS entry was not stored.')

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

    def test_03_abbo_permissions(self):
        member = cli_user('rss_member')
        server = member.get_server()
        private_channel = server.get_or_create_channel(member.get_name())
        public_channel = server.get_or_create_channel('rss_public')
        self.assertTrue(abbo().env_channel(private_channel).gdo_has_permission(member))
        self.assertFalse(abbo().env_channel(public_channel).gdo_has_permission(member))

    def test_04_timer_reloads_entries(self):
        feed = GDO_RSSFeed.table().get_by_vals({'rss_name': 'hackernews'})
        entry = GDO_RSSEntry.table().select().where(f'rse_feed={feed.get_id()}').order('rse_id DESC').first().exec().fetch_object()
        entry.delete()
        self.assertIsNone(GDO_RSSEntry.table().get_by_id(entry.get_id()), 'RSS entry was not deleted.')

        module = module_rss.instance()
        feed.save_val('rss_last_check', Time.get_date(Application.TIME - module.cfg_check_sleep() - 1))
        reloaded = RSSParsedEntry(entry.gdo_val('rse_uid'), entry.gdo_val('rse_title'), entry.gdo_val('rse_url'), entry.gdo_value('rse_published'))
        with patch.object(GDO_RSSFeed, 'load_entries', new=AsyncMock(return_value=[reloaded])):
            Application.EVENTS.reset_timers()
            module.gdo_subscribe_events()
            Application.LOOP.run_until_complete(Application.EVENTS.update_timers(Application.TIME + module.cfg_check_sleep()))
        self.assertIsNotNone(GDO_RSSEntry.table().get_by_vals({
            'rse_feed': feed.get_id(),
            'rse_uid': reloaded.uid,
        }), 'Timer did not restore the deleted RSS entry.')

    def test_05_news_cli(self):
        giz = cli_gizmore()
        feed = GDO_RSSFeed.table().get_by_vals({'rss_name': 'hackernews'})
        now = datetime.now(timezone.utc)
        feed.store_entries([
            RSSParsedEntry('hn-news-2', 'Second entry', 'https://example.com/2', now + timedelta(seconds=1)),
            RSSParsedEntry('hn-news-3', 'Third entry', 'https://example.com/3', now + timedelta(seconds=2)),
        ])
        out = cli_plug(giz, '$rss.news --limit=10 hackernews')
        for title in ('Third entry', 'Second entry', 'Initial entry'):
            entry = GDO_RSSEntry.table().get_by_vals({'rse_title': title})
            rendered = f'{Render.bold(entry.get_id(), Mode.render_cli)}-{title}'
            self.assertIn(rendered, out, 'RSS news did not render the persistent entry ID.')
        self.assertEqual(TableMode.CARDS, news().gdo_table_mode(), 'RSS news is not rendered as cards.')
        entry = GDO_RSSEntry.table().select().where("rse_title='Initial entry'").first().exec().fetch_object()
        self.assertIn('Initial entry', entry.render_card(), 'RSS entry card did not render its title.')

    def test_06_parse_rss(self):
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

    def test_07_parse_atom(self):
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
