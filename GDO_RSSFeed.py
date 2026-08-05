import asgiref.sync
import httplib2

from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Deletor import GDT_Deletor
from gdo.core.GDT_Name import GDT_Name
from gdo.date.GDT_Created import GDT_Created
from gdo.date.GDT_DateTime import GDT_DateTime
from gdo.date.GDT_Deleted import GDT_Deleted
from gdo.date.GDT_Timestamp import GDT_Timestamp
from gdo.date.Time import Time
from gdo.net.GDT_Url import GDT_Url
from gdo.rss.RSSParser import RSSParser


class GDO_RSSFeed(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('rss_id'),
            GDT_Name('rss_name').not_null().unique(),
            GDT_Url('rss_url').not_null().unique(),
            GDT_Creator('rss_creator'),
            GDT_Created('rss_created'),
            GDT_Deleted('rss_deleted'),
            GDT_Deletor('rss_deletor'),
            GDT_DateTime('rss_last_change'),
            GDT_Timestamp('rss_last_check'),
        ]

    def render_name(self) -> str:
        return self.gdo_val('rss_name')

    def get_url(self) -> str:
        return self.gdo_val('rss_url')

    @classmethod
    async def load_entries(cls, url: str):
        response, content = await asgiref.sync.SyncToAsync(cls._load_url)(url)
        if response.status >= 400:
            raise ValueError(f'HTTP {response.status} while loading {url}')
        return RSSParser.parse(content)

    async def check_feed(self) -> int:
        checked = Time.get_date()
        try:
            added = self.store_entries(await self.load_entries(self.get_url()))
            if added:
                self.save_val('rss_last_change', checked)
            return added
        except Exception as error:
            Logger.exception(error)
            return 0
        finally:
            self.save_val('rss_last_check', checked)

    @staticmethod
    def _load_url(url: str):
        return httplib2.Http(timeout=10).request(url, method='GET', headers={
            'accept': 'application/atom+xml, application/rss+xml, application/xml, text/xml',
        })

    def store_entries(self, entries) -> int:
        from gdo.rss.GDO_RSSEntry import GDO_RSSEntry
        added = 0
        table = GDO_RSSEntry.table()
        for entry in entries:
            if table.get_by_vals({'rse_feed': self.get_id(), 'rse_uid': entry.uid}):
                continue
            table.blank({
                'rse_feed': self.get_id(),
                'rse_uid': entry.uid,
                'rse_title': entry.title,
                'rse_url': entry.url,
                'rse_published': Time.get_date(entry.published.timestamp()) if entry.published else None,
            }).insert()
            added += 1
        return added
