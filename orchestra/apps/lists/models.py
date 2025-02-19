from django.db import models
from django.utils.translation import ugettext_lazy as _

from orchestra.core import services
from orchestra.core.validators import validate_name

from . import settings


class List(models.Model):
    name = models.CharField(_("name"), max_length=128, unique=True,
            validators=[validate_name])
    address_name = models.CharField(_("address name"), max_length=128,
            validators=[validate_name], blank=True)
    address_domain = models.ForeignKey(settings.LISTS_DOMAIN_MODEL,
            verbose_name=_("address domain"), blank=True, null=True)
    admin_email = models.EmailField(_("admin email"),
            help_text=_("Administration email address"))
    account = models.ForeignKey('accounts.Account', verbose_name=_("Account"),
            related_name='lists')
    
    class Meta:
        unique_together = ('address_name', 'address_domain')
    
    def __unicode__(self):
        return "%s@%s" % (self.address_name, self.address_domain)
    
    def get_username(self):
        return self.name
    
    def set_password(self, password):
        self.password = password


services.register(List)
