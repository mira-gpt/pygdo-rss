from gdo.base.Logger import Logger
from gdo.base.Util import html
from gdo.date.Time import Time
from gdo.form.GDT_Form import GDT_Form
from gdo.form.MethodForm import MethodForm
from gdo.rss.GDO_RSSFeed import GDO_RSSFeed


class add(MethodForm):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'rss.add'

    def gdo_create_form(self, form: GDT_Form) -> None:
        feed = GDO_RSSFeed.blank()
        form.add_fields(
            feed.column('rss_name').label('name'),
            feed.column('rss_url').label('url').external().schemes(['http', 'https']),
        )
        super().gdo_create_form(form)

    async def form_submitted(self):
        url = self.param_val('rss_url')
        try:
            entries = await GDO_RSSFeed.load_entries(url)
        except Exception:
            try:
                urls = await GDO_RSSFeed.discover_urls(url)
            except Exception as error:
                Logger.exception(error)
                return self.err('err_rss_unreadable')
            if not urls:
                return self.err('err_rss_unreadable')
            if len(urls) > 1:
                return self.err('err_rss_multiple', (html(', '.join(urls)),))
            url = urls[0]
            try:
                entries = await GDO_RSSFeed.load_entries(url)
            except Exception as error:
                Logger.exception(error)
                return self.err('err_rss_unreadable')

        checked = Time.get_date()
        feed = GDO_RSSFeed.blank({
            'rss_name': self.param_val('rss_name'),
            'rss_url': url,
        }).insert()
        if feed.store_entries(entries):
            feed.save_val('rss_last_change', checked)
        feed.save_val('rss_last_check', checked)
        return self.msg('msg_rss_added', (feed.render_name(),))
