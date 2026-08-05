from gdo.base.GDT import GDT
from gdo.base.Query import Query
from gdo.base.GDO import GDO
from gdo.base.Render import Mode, Render
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_UInt import GDT_UInt
from gdo.rss.GDO_RSSEntry import GDO_RSSEntry
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed
from gdo.table.MethodQueryCards import MethodQueryCards


class news(MethodQueryCards):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'rss.news'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_UInt('limit').not_null().initial('10').min(1).max(100),
            GDT_Object('feed').table(GDO_RSSFeed.table()).not_null(),
        ]

    def gdo_table(self) -> GDO:
        return GDO_RSSEntry.table()

    def gdo_table_query(self) -> Query:
        feed = self.param_value('feed')
        return (self.gdo_table().select().
                where(f'rse_feed={feed.get_id()}').
                order('rse_published DESC, rse_id DESC').
                limit(self.param_value('limit')))

    def gdo_paginated(self) -> bool:
        return False

    def gdo_ordered(self) -> bool:
        return False

    def gdo_filtered(self) -> bool:
        return False

    def gdo_searched(self) -> bool:
        return False

    def render_gdo(self, gdo: GDO, mode: Mode) -> str:
        if mode == Mode.render_json:
            return super().render_gdo(gdo, mode)
        return f'{Render.bold(gdo.get_id(), mode)}-{gdo.render_name()}'
