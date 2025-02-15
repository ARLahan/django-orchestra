import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from orchestra.core import validators, services
from orchestra.utils.functional import cached

from . import settings


def settings_to_choices(choices):
    return sorted(
        [ (name, opt[0]) for name,opt in choices.iteritems() ],
        key=lambda e: e[0]
    )


class Website(models.Model):
    name = models.CharField(_("name"), max_length=128, unique=True,
            validators=[validators.validate_name])
    account = models.ForeignKey('accounts.Account', verbose_name=_("Account"),
            related_name='websites')
    port = models.PositiveIntegerField(_("port"),
            choices=settings.WEBSITES_PORT_CHOICES,
            default=settings.WEBSITES_DEFAULT_PORT)
    domains = models.ManyToManyField(settings.WEBSITES_DOMAIN_MODEL,
            related_name='websites', verbose_name=_("domains"))
    contents = models.ManyToManyField('webapps.WebApp', through='websites.Content')
    is_active = models.BooleanField(_("is active"), default=True)
    
    def __unicode__(self):
        return self.name
    
    @property
    def unique_name(self):
        return "%s-%s" % (self.account, self.name)
    
    @cached
    def get_options(self):
        return { opt.name: opt.value for opt in self.options.all() }
    
    @property
    def protocol(self):
        if self.port == 80:
            return 'http'
        if self.port == 443:
            return 'https'
        raise TypeError('No protocol for port "%s"' % self.port)


class WebsiteOption(models.Model):
    website = models.ForeignKey(Website, verbose_name=_("web site"),
            related_name='options')
    name = models.CharField(_("name"), max_length=128,
            choices=settings_to_choices(settings.WEBSITES_OPTIONS))
    value = models.CharField(_("value"), max_length=256)
    
    class Meta:
        unique_together = ('website', 'name')
        verbose_name = _("option")
        verbose_name_plural = _("options")
    
    def __unicode__(self):
        return self.name
    
    def clean(self):
        """ validates name and value according to WEBSITES_WEBSITEOPTIONS """
        __, regex = settings.WEBSITES_OPTIONS[self.name]
        if not re.match(regex, self.value):
            msg = _("'%s' does not match %s")
            raise ValidationError(msg % (self.value, regex))


class Content(models.Model):
    webapp = models.ForeignKey('webapps.WebApp', verbose_name=_("web application"))
    website = models.ForeignKey('websites.Website', verbose_name=_("web site"))
    path = models.CharField(_("path"), max_length=256, blank=True)
    
    class Meta:
        unique_together = ('website', 'path')
    
    def clean(self):
        if not self.path.startswith('/'):
            self.path = '/' + self.path
    
    def __unicode__(self):
        return self.website.name + self.path


services.register(Website)
