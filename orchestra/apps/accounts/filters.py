from django.contrib.admin import SimpleListFilter
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _


class HasMainUserListFilter(SimpleListFilter):
    """ Filter Nodes by group according to request.user """
    title = _("has main user")
    parameter_name = 'mainuser'
    
    def lookups(self, request, model_admin):
        return (
            ('True', _("Yes")),
            ('False', _("No")),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(users__isnull=False).distinct()
        if self.value() == 'False':
            return queryset.filter(users__isnull=True).distinct()
