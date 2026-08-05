from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_Unique import GDT_Unique
from gdo.date.GDT_Created import GDT_Created
from gdo.date.GDT_DateTime import GDT_DateTime
from gdo.net.GDT_Url import GDT_Url
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed
from gdo.ui.GDT_Title import GDT_Title


class GDO_RSSEntry(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('rse_id'),
            GDT_Object('rse_feed').table(GDO_RSSFeed.table()).not_null().cascade_delete(),
            GDT_String('rse_uid').maxlen(512).not_null(),
            GDT_Title('rse_title').maxlen(256).not_null(),
            GDT_Url('rse_url'),
            GDT_DateTime('rse_published'),
            GDT_Created('rse_fetched'),
            GDT_Unique('unique_feed_uid').unique_columns('rse_feed', 'rse_uid'),
        ]

    def render_name(self) -> str:
        return self.gdo_val('rse_title')
