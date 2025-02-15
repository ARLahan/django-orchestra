from admin_tools.menu import items, Menu
from django.core.urlresolvers import reverse
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from orchestra.core import services, accounts
from orchestra.utils.apps import isinstalled


def api_link(context):
    """ Dynamically generates API related URL """
    if 'opts' in context:
        opts = context['opts']
    elif 'cl' in context:
        opts = context['cl'].opts
    else:
        return reverse('api-root')
    if 'object_id' in context: 
        object_id = context['object_id']
        try:
            return reverse('%s-detail' % opts.model_name, args=[object_id])
        except:
            return reverse('api-root')
    try:
        return reverse('%s-list' % opts.model_name)
    except:
        return reverse('api-root')


def get_services():
    childrens = []
    for model, options in services.get().iteritems():
        if options.get('menu', True):
            opts = model._meta
            url = reverse('admin:{}_{}_changelist'.format(
                    opts.app_label, opts.model_name))
            name = capfirst(options.get('verbose_name_plural'))
            childrens.append(items.MenuItem(name, url))
    return sorted(childrens, key=lambda i: i.title)


def get_accounts():
    childrens = [
        items.MenuItem(_("Accounts"),
                       reverse('admin:accounts_account_changelist'))
    ]
    if isinstalled('orchestra.apps.users'):
        url = reverse('admin:users_user_changelist')
        childrens.append(items.MenuItem(_("Users"), url))
    if isinstalled('orchestra.apps.payments'):
        url = reverse('admin:payments_transactionprocess_changelist')
        childrens.append(items.MenuItem(_("Transaction processes"), url))
    if isinstalled('orchestra.apps.issues'):
        url = reverse('admin:issues_ticket_changelist')
        childrens.append(items.MenuItem(_("Tickets"), url))
    for model, options in accounts.get().iteritems():
        if options.get('menu', True):
            opts = model._meta
            url = reverse('admin:{}_{}_changelist'.format(
                    opts.app_label, opts.model_name))
            name = capfirst(options.get('verbose_name_plural'))
            childrens.append(items.MenuItem(name, url))
    return sorted(childrens, key=lambda i: i.title)


def get_administration_items():
    childrens = []
    if isinstalled('orchestra.apps.orders'):
        url = reverse('admin:orders_service_changelist')
        childrens.append(items.MenuItem(_("Services"), url))
    if isinstalled('orchestra.apps.orchestration'):
        route = reverse('admin:orchestration_route_changelist')
        backendlog = reverse('admin:orchestration_backendlog_changelist')
        server = reverse('admin:orchestration_server_changelist')
        childrens.append(items.MenuItem(_("Orchestration"), route, children=[
            items.MenuItem(_("Routes"), route),
            items.MenuItem(_("Backend logs"), backendlog),
            items.MenuItem(_("Servers"), server),
        ]))
    if isinstalled('orchestra.apps.resources'):
        resource = reverse('admin:resources_resource_changelist')
        data = reverse('admin:resources_resourcedata_changelist')
        monitor = reverse('admin:resources_monitordata_changelist')
        childrens.append(items.MenuItem(_("Resources"), resource, children=[
            items.MenuItem(_("Resources"), resource),
            items.MenuItem(_("Data"), data),
            items.MenuItem(_("Monitoring"), monitor),
        ]))
    if isinstalled('orchestra.apps.miscellaneous'):
        url = reverse('admin:miscellaneous_miscservice_changelist')
        childrens.append(items.MenuItem(_("Miscellaneous"), url))
    if isinstalled('orchestra.apps.issues'):
        url = reverse('admin:issues_queue_changelist')
        childrens.append(items.MenuItem(_("Ticket queues"), url))
    if isinstalled('djcelery'):
        task = reverse('admin:djcelery_taskstate_changelist')
        periodic = reverse('admin:djcelery_periodictask_changelist')
        worker = reverse('admin:djcelery_workerstate_changelist')
        childrens.append(items.MenuItem(_("Celery"), task, children=[
            items.MenuItem(_("Tasks"), task),
            items.MenuItem(_("Periodic tasks"), periodic),
            items.MenuItem(_("Workers"), worker),
        ]))
    return childrens


class OrchestraMenu(Menu):
    def init_with_context(self, context):
        self.children += [
            items.MenuItem(
                _('Dashboard'),
                reverse('admin:index')
            ),
            items.Bookmarks(),
            items.MenuItem(
                _("Services"),
                reverse('admin:index'),
                children=get_services()
            ),
            items.MenuItem(
                _("Accounts"),
                reverse('admin:accounts_account_changelist'),
                children=get_accounts()
            ),
            items.MenuItem(
                _("Administration"),
                children=get_administration_items()
            ),
            items.MenuItem("API", api_link(context))
        ]
