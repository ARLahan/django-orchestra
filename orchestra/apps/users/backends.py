import textwrap

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from orchestra.apps.orchestration import ServiceController
from orchestra.apps.resources import ServiceMonitor

from . import settings


class SystemUserBackend(ServiceController):
    verbose_name = _("System User")
    model = 'users.User'
    ignore_fields = ['last_login']
    
    def save(self, user):
        context = self.get_context(user)
        if user.is_main:
            self.append(textwrap.dedent("""
                if [[ $( id %(username)s ) ]]; then
                   usermod --password '%(password)s' %(username)s
                else
                   useradd %(username)s --password '%(password)s' \\
                         --shell /bin/false
                fi
                mkdir -p %(home)s
                chown %(username)s.%(username)s %(home)s""" % context
            ))
        else:
            self.delete(user)
    
    def delete(self, user):
        context = self.get_context(user)
        self.append("{ sleep 2 && killall -u %(username)s -s KILL; } &" % context)
        self.append("killall -u %(username)s" % context)
        self.append("userdel %(username)s" % context)
    
    def get_context(self, user):
        context = {
            'username': user.username,
            'password': user.password if user.is_active else '*%s' % user.password,
        }
        context['home'] = settings.USERS_SYSTEMUSER_HOME % context
        return context


class SystemUserDisk(ServiceMonitor):
    model = 'users.User'
    resource = ServiceMonitor.DISK
    verbose_name = _('System user disk')
    
    def monitor(self, user):
        context = self.get_context(user)
        self.append("du -s %(home)s | xargs echo %(object_id)s" % context)
    
    def get_context(self, user):
        context = SystemUserBackend().get_context(user)
        context['object_id'] = user.pk
        return context


class FTPTraffic(ServiceMonitor):
    model = 'users.User'
    resource = ServiceMonitor.TRAFFIC
    verbose_name = _('FTP traffic')
    
    def prepare(self):
        current_date = timezone.localtime(self.current_date)
        current_date = current_date.strftime("%Y%m%d%H%M%S")
        self.append(textwrap.dedent("""
            function monitor () {
                OBJECT_ID=$1
                INI_DATE=$2
                USERNAME="$3"
                LOG_FILE="$4"
                grep "UPLOAD\|DOWNLOAD" "${LOG_FILE}" \\
                    | grep " \\[${USERNAME}\\] " \\
                    | awk -v ini="${INI_DATE}" '
                        BEGIN {
                            end = "%s"
                            sum = 0
                            months["Jan"] = "01"
                            months["Feb"] = "02"
                            months["Mar"] = "03"
                            months["Apr"] = "04"
                            months["May"] = "05"
                            months["Jun"] = "06"
                            months["Jul"] = "07"
                            months["Aug"] = "08"
                            months["Sep"] = "09"
                            months["Oct"] = "10"
                            months["Nov"] = "11"
                            months["Dec"] = "12"
                        } {
                            # log: Fri Jul 11 13:23:17 2014
                            split($4, t, ":")
                            # line_date = year month day hour minute second
                            line_date = $5 months[$2] $3 t[1] t[2] t[3]
                            if ( line_date > ini && line_date < end)
                                split($0, l, "\\", ")
                                split(l[3], b, " ")
                                sum += b[1]
                        } END {
                            print sum
                        }
                    ' | xargs echo ${OBJECT_ID}
            }""" % current_date))
    
    def monitor(self, user):
        context = self.get_context(user)
        self.append(
            'monitor %(object_id)i %(last_date)s "%(username)s" "%(log_file)s"' % context)
    
    def get_context(self, user):
        last_date = timezone.localtime(self.get_last_date(user.pk))
        return {
            'log_file': settings.USERS_FTP_LOG_PATH,
            'last_date': last_date.strftime("%Y%m%d%H%M%S"),
            'object_id': user.pk,
            'username': user.username,
        }
    
