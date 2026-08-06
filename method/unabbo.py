from gdo.rss.GDO_RSSAbbo import GDO_RSSAbbo
from gdo.rss.method.abbo import abbo


class unabbo(abbo):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'rss.unabbo'

    def gdo_execute(self):
        feed = self.param_value('feed')
        where = f'rsa_feed={feed.get_id()}'
        if self.is_private_context(self._env_user):
            where += f' AND rsa_user={self._env_user.get_id()} AND rsa_channel IS NULL'
        else:
            where += f' AND rsa_channel={self._env_channel.get_id()} AND rsa_user IS NULL'
        if not (abbo := GDO_RSSAbbo.table().select().where(where).first().exec().fetch_object()):
            return self.err('err_rss_not_subscribed', (feed.render_name(),))
        abbo.delete()
        return self.reply('msg_rss_unsubscribed', (feed.render_name(),))
