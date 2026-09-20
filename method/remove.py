from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Object import GDT_Object
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed


class remove(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'rss.del'

    def gdo_method_hidden(self) -> bool:
        return True

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Object('feed').table(GDO_RSSFeed.table()).not_null(),
        ]

    def gdo_has_permission(self, user) -> bool:
        return user.is_member()

    def gdo_execute(self) -> GDT:
        feed = self.param_value('feed')
        user = self._env_user
        if not user.is_staff() and feed.gdo_val('rss_creator') != user.get_id():
            return self.err_generic_permission()
        name = feed.render_name()
        feed.delete()
        return self.reply('msg_rss_deleted', (name,))
