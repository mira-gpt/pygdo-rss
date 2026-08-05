from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Channel import GDT_Channel
from gdo.core.GDT_Creator import GDT_Creator
from gdo.core.GDT_Object import GDT_Object
from gdo.core.GDT_Unique import GDT_Unique
from gdo.core.GDT_User import GDT_User
from gdo.date.GDT_Created import GDT_Created
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed


class GDO_RSSAbbo(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('rsa_id'),
            GDT_Object('rsa_feed').table(GDO_RSSFeed.table()).not_null().cascade_delete(),
            GDT_User('rsa_user'),
            GDT_Channel('rsa_channel'),
            GDT_Created('rsa_created'),
            GDT_Creator('rsa_creator'),
            GDT_Unique('unique_user').unique_columns('rsa_user', 'rsa_feed'),
            GDT_Unique('unique_channel').unique_columns('rsa_channel', 'rsa_feed'),
        ]

    def get_user(self) -> GDO_User:
        return self.gdo_value('rsa_user')

    def get_channel(self) -> GDO_Channel:
        return self.gdo_value('rsa_channel')
