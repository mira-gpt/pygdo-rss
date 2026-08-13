from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.rss.GDO_RSSAbbo import GDO_RSSAbbo
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed


class rss(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'rss'

    def gdo_execute(self) -> GDT:
        feeds = GDO_RSSFeed.table().count_where('rss_deleted IS NULL')
        subscriptions = GDO_RSSAbbo.table().count_where(self.gdo_subscription_where())
        return self.reply('msg_rss_overview', (feeds, subscriptions))

    def gdo_subscription_where(self) -> str:
        """Count subscriptions for the user or channel the command came from."""
        if self._env_channel and self._env_channel.get_name() != self._env_user.get_name():
            return f'rsa_channel={self._env_channel.get_id()} AND rsa_user IS NULL'
        return f'rsa_user={self._env_user.get_id()} AND rsa_channel IS NULL'
