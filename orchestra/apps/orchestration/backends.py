from functools import partial

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from orchestra.utils import plugins

from . import methods


class ServiceBackend(plugins.Plugin):
    """
    Service management backend base class
    
    It uses the _unit of work_ design principle, which allows bulk operations to
    be conviniently supported. Each backend generates the configuration for all
    the changes of all modified objects, reloading the daemon just once.
    """
    model = None
    related_models = () # ((model, accessor__attribute),)
    script_method = methods.BashSSH
    function_method = methods.Python
    type = 'task' # 'sync'
    ignore_fields = []
    actions = []
    
    # TODO type: 'script', execution:'task'
    
    __metaclass__ = plugins.PluginMount
    
    def __unicode__(self):
        return type(self).__name__
    
    def __str__(self):
        return unicode(self)
    
    def __init__(self):
        self.cmds = []
    
    @classmethod
    def get_actions(cls):
        return [ action for action in cls.actions if action in dir(cls) ]
    
    @classmethod
    def get_name(cls):
        return cls.__name__
    
    @classmethod
    def is_main(cls, obj):
        opts = obj._meta
        return cls.model == '%s.%s' % (opts.app_label, opts.object_name)
    
    @classmethod
    def get_related(cls, obj):
        opts = obj._meta
        model = '%s.%s' % (opts.app_label, opts.object_name)
        for rel_model, field in cls.related_models:
            if rel_model == model:
                related = obj
                for attribute in field.split('__'):
                    related = getattr(related, attribute)
                return related
        return None
    
    @classmethod
    def get_backends(cls):
        return cls.get_plugins()
    
    @classmethod
    def get_backend(cls, name):
        return cls.get_plugin(name)
    
    def get_banner(self):
        time = timezone.now().strftime("%h %d, %Y %I:%M:%S")
        return "Generated by Orchestra %s" % time
    
    def execute(self, server):
        from .models import BackendLog
        state = BackendLog.STARTED if self.cmds else BackendLog.SUCCESS
        log = BackendLog.objects.create(backend=self.get_name(), state=state, server=server)
        for method, cmds in self.cmds:
            method(log, server, cmds)
            if log.state != BackendLog.SUCCESS:
                break
        return log
    
    def append(self, *cmd):
        # aggregate commands acording to its execution method
        if isinstance(cmd[0], basestring):
            method = self.script_method
            cmd = cmd[0]
        else:
            method = self.function_method
            cmd = partial(*cmd)
        if not self.cmds or self.cmds[-1][0] != method:
            self.cmds.append((method, [cmd]))
        else:
            self.cmds[-1][1].append(cmd)
    
    def prepare(self):
        """ hook for executing something at the beging """
        pass
    
    def commit(self):
        """
        apply the configuration, usually reloading a service 
        reloading a service is done in a separated method in order to reload 
        the service once in bulk operations
        """
        pass


class ServiceController(ServiceBackend):
    actions = ('save', 'delete')
    
    @classmethod
    def get_backends(cls):
        """ filter controller classes """
        return [
            plugin for plugin in cls.plugins if ServiceController in plugin.__mro__
        ]
