from __future__ import annotations

from gdo.base.Application import Application
from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.GDO_Module import GDO_Module
from gdo.date.GDT_Duration import GDT_Duration
from gdo.date.Time import Time
from gdo.rss.GDO_RSSAbbo import GDO_RSSAbbo
from gdo.rss.GDO_RSSEntry import GDO_RSSEntry
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed


class module_rss(GDO_Module):

    def gdo_dependencies(self) -> list:
        return [
            'core',
        ]

    def gdo_classes(self) -> list[type[GDO]]:
        return [
            GDO_RSSFeed,
            GDO_RSSAbbo,
            GDO_RSSEntry,
        ]

    def gdo_module_config(self) -> list[GDT]:
        return [
            GDT_Duration('rss_check_sleep').not_null().min(30).max(Time.ONE_WEEK).initial('5m'),
        ]

    def cfg_check_sleep(self) -> float:
        return self.get_config_value('rss_check_sleep')

    def gdo_subscribe_events(self):
        Application.EVENTS.add_timer(self.cfg_check_sleep(), self.rss_timer)

    async def rss_timer(self):
        sleep = self.cfg_check_sleep()
        try:
            cut = Time.get_date(Application.TIME - sleep)
            if feed := (GDO_RSSFeed.table().select().
                        where("rss_deleted IS NULL").
                        where(f"(rss_last_check IS NULL OR rss_last_check < '{cut}')").
                        order('rss_last_check IS NOT NULL, rss_last_check').
                        limit(1).
                        first().exec().fetch_object()):
                if entries := await feed.check_feed():
                    await self.announce_entries(feed, entries)
        finally:
            Application.EVENTS.add_timer(sleep, self.rss_timer)

    async def announce_entries(self, feed: GDO_RSSFeed, entries: list[GDO_RSSEntry]):
        subscriptions = (GDO_RSSAbbo.table().select().
                         where(f'rsa_feed={feed.get_id()}').exec().fetch_all())
        for subscription in subscriptions:
            channel = subscription.get_channel()
            user = subscription.get_user()
            for entry in entries:
                args = (feed.render_name(), entry.render_name(), entry.gdo_val('rse_url') or '')
                if channel:
                    await channel.send_text('msg_rss_entry', args)
                elif user:
                    await user.send('msg_rss_entry', args)
