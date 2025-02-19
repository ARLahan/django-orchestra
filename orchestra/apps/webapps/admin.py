from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from orchestra.admin import ExtendedModelAdmin
from orchestra.apps.accounts.admin import SelectAccountAdminMixin

from .models import WebApp, WebAppOption


class WebAppOptionInline(admin.TabularInline):
    model = WebAppOption
    extra = 1
    
    class Media:
        css = {
            'all': ('orchestra/css/hide-inline-id.css',)
        }
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        """ Make value input widget bigger """
        if db_field.name == 'value':
            kwargs['widget'] = forms.TextInput(attrs={'size':'100'})
        return super(WebAppOptionInline, self).formfield_for_dbfield(db_field, **kwargs)


class WebAppAdmin(SelectAccountAdminMixin, ExtendedModelAdmin):
    fields = ('account_link', 'name', 'type')
    list_display = ('name', 'type', 'display_websites', 'account_link')
    list_filter = ('type',)
    inlines = [WebAppOptionInline]
    readonly_fields = ('account_link',)
    change_readonly_fields = ('name', 'type')
    
    def display_websites(self, webapp):
        websites = []
        for content in webapp.content_set.all().select_related('website'):
            website = content.website
            url = reverse('admin:websites_website_change', args=(website.pk,))
            name = "%s on %s" % (website.name, content.path)
            websites.append('<a href="%s">%s</a>' % (url, name))
        return '<br>'.join(websites)
    display_websites.short_description = _("web sites")
    display_websites.allow_tags = True


admin.site.register(WebApp, WebAppAdmin)
