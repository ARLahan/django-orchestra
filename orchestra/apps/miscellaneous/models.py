from django.db import models
from django.utils.translation import ugettext_lazy as _

from orchestra.core import services


class MiscService(models.Model):
    name = models.CharField(_("name"), max_length=256)
    description = models.TextField(blank=True)
    has_amount = models.BooleanField(default=False,
            help_text=_("Designates whether this service has <tt>amount</tt> "
                        "property or not."))
    is_active = models.BooleanField(default=True,
            help_text=_("Whether new instances of this service can be created "
                        "or not. Unselect this instead of deleting services."))
    
    def __unicode__(self):
        return self.name


class Miscellaneous(models.Model):
    service = models.ForeignKey(MiscService, verbose_name=_("service"),
            related_name='instances')
    account = models.ForeignKey('accounts.Account', verbose_name=_("account"),
            related_name='miscellaneous')
    description = models.TextField(_("description"), blank=True)
    amount = models.PositiveIntegerField(_("amount"), default=1)
    is_active = models.BooleanField(default=True,
            help_text=_("Designates whether this service should be treated as "
                        "active. Unselect this instead of deleting services."))
    
    class Meta:
        verbose_name_plural = _("miscellaneous")
    
    def __unicode__(self):
        return "{0}-{1}".format(str(self.service), str(self.account))


services.register(Miscellaneous)
