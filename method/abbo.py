from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Object import GDT_Object
from gdo.rss.GDO_RSSAbbo import GDO_RSSAbbo
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed


class abbo(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'rss.abbo'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('feed').table(GDO_RSSFeed.table()).not_null(),
        ]

    def gdo_has_permission(self, user) -> bool:
        return user.is_staff() if self._env_channel else user.is_human()

    def gdo_execute(self) -> GDT:
        feed = self.param_value('feed')
        GDO_RSSAbbo.blank({
            'rsa_feed': feed.get_id(),
            'rsa_user': None if self._env_channel else self._env_user.get_id(),
            'rsa_channel': self._env_channel.get_id() if self._env_channel else None,
        }).insert()
        return self.reply('msg_rss_subscribed', (feed.render_name(),))
