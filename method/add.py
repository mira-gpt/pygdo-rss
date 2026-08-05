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

    def form_submitted(self):
        feed = GDO_RSSFeed.blank({
            'rss_name': self.param_val('rss_name'),
            'rss_url': self.param_val('rss_url'),
            'rss_last_change': Time.get_date(),
        }).insert()
        return self.msg('msg_rss_added', (feed.render_name(),))
