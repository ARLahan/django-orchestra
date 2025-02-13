# Django settings for orchestra project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Enable persistent connections
CONN_MAX_AGE = 60*10

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

MEDIA_URL = '/media/'

ALLOWED_HOSTS = '*'

# Set this to True to wrap each HTTP request in a transaction on this database.
ATOMIC_REQUESTS = True

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'orchestra.core.cache.RequestCacheMiddleware',
    'orchestra.apps.orchestration.middlewares.OperationsMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


TEMPLATE_CONTEXT_PROCESSORS =(
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "orchestra.core.context_processors.site",
)


INSTALLED_APPS = (
    # django-orchestra apps
    'orchestra',
    'orchestra.apps.orchestration',
    'orchestra.apps.domains',
    'orchestra.apps.users',
#    'orchestra.apps.users.roles.mail',
    'orchestra.apps.users.roles.jabber',
    'orchestra.apps.users.roles.posix',
    'orchestra.apps.mails',
    'orchestra.apps.lists',
    'orchestra.apps.webapps',
    'orchestra.apps.websites',
    'orchestra.apps.databases',
    'orchestra.apps.vps',
    'orchestra.apps.issues',
    'orchestra.apps.orders',
    'orchestra.apps.miscellaneous',
    'orchestra.apps.bills',
    'orchestra.apps.payments',
    
    # Third-party apps
    'django_extensions',
    'djcelery',
    'djcelery_email',
    'fluent_dashboard',
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    'rest_framework',
    'rest_framework.authtoken',
    'passlib.ext.django',
    
    # Django.contrib
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    
    'orchestra.apps.accounts',
    'orchestra.apps.contacts',
    'orchestra.apps.resources',
)


AUTH_USER_MODEL = 'users.User'


AUTHENTICATION_BACKENDS = [
    'orchestra.permissions.auth.OrchestraPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
]


#TODO  Email config
#EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'


#################################
## 3RD PARTY APPS CONIGURATION ##
#################################

# Admin Tools
ADMIN_TOOLS_MENU = 'orchestra.admin.menu.OrchestraMenu'

# Fluent dashboard
# TODO subclass like in admin_tools_menu
ADMIN_TOOLS_INDEX_DASHBOARD = 'fluent_dashboard.dashboard.FluentIndexDashboard'
FLUENT_DASHBOARD_ICON_THEME = '../orchestra/icons'

FLUENT_DASHBOARD_APP_GROUPS = (
    # Services group is generated by orchestra.admin.dashboard
    ('Accounts', {
        'models': (
            'orchestra.apps.accounts.models.Account',
            'orchestra.apps.contacts.models.Contact',
            'orchestra.apps.users.models.User',
            'orchestra.apps.orders.models.Order',
            'orchestra.apps.orders.models.Plan',
            'orchestra.apps.bills.models.Bill',
#            'orchestra.apps.payments.models.PaymentSource',
            'orchestra.apps.payments.models.Transaction',
            'orchestra.apps.issues.models.Ticket',
        ),
        'collapsible': True,
    }),
    ('Administration', {
        'models': (
            'djcelery.models.TaskState',
            'orchestra.apps.orchestration.models.Route',
            'orchestra.apps.orchestration.models.BackendLog',
            'orchestra.apps.orchestration.models.Server',
            'orchestra.apps.resources.models.Resource',
            'orchestra.apps.resources.models.Monitor',
            'orchestra.apps.orders.models.Service',
        ),
        'collapsible': True,
    }),
)

FLUENT_DASHBOARD_APP_ICONS = {
    # Services
    'webs/web': 'web.png',
    'mail/address': 'X-office-address-book.png',
    'mails/mailbox': 'email.png',
    'mails/address': 'X-office-address-book.png',
    'lists/list': 'email-alter.png',
    'domains/domain': 'domain.png',
    'multitenance/tenant': 'apps.png',
    'webapps/webapp': 'Applications-other.png',
    'websites/website': 'Applications-internet.png',
    'databases/database': 'database.png',
    'databases/databaseuser': 'postgresql.png',
    'vps/vps': 'TuxBox.png',
    'miscellaneous/miscellaneous': 'applications-other.png',
    # Accounts
    'accounts/account': 'Face-monkey.png',
    'contacts/contact': 'contact_book.png',
    'orders/order': 'basket.png',
    'orders/service': 'price.png',
    'orders/plan': 'Pack.png',
    'bills/bill': 'invoice.png',
    'payments/paymentsource': 'card_in_use.png',
    'payments/transaction': 'transaction.png',
    'issues/ticket': 'Ticket_star.png',
    # Administration
    'users/user': 'Mr-potato.png',
    'djcelery/taskstate': 'taskstate.png',
    'orchestration/server': 'vps.png',
    'orchestration/route': 'hal.png',
    'orchestration/backendlog': 'scriptlog.png',
    'resources/resource': "gauge.png",
    'resources/monitor': "Utilities-system-monitor.png",
}

# Django-celery
import djcelery
djcelery.setup_loader()
# Broker
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_SEND_EVENTS = True
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_DISABLE_RATE_LIMITS = True
# Do not fill the logs with crap
CELERY_REDIRECT_STDOUTS_LEVEL = 'DEBUG'


# rest_framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'orchestra.permissions.api.OrchestraPermissionBackend',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        ('rest_framework.filters.DjangoFilterBackend',)
    ),
}


# Use a UNIX compatible hash
PASSLIB_CONFIG = (
    "[passlib]\n"
    "schemes = sha512_crypt, django_pbkdf2_sha256, django_pbkdf2_sha1,"
    "        django_bcrypt, django_bcrypt_sha256, django_salted_sha1, des_crypt,"
    "        django_salted_md5, django_des_crypt, hex_md5, bcrypt, phpass\n"
    "default = sha512_crypt\n"
    "deprecated = django_pbkdf2_sha1, django_salted_sha1, django_salted_md5,"
    "        django_des_crypt, des_crypt, hex_md5\n"
    "all__vary_rounds = 0.05\n"
    "django_pbkdf2_sha256__min_rounds = 10000\n"
    "sha512_crypt__min_rounds = 80000\n"
    "staff__django_pbkdf2_sha256__default_rounds = 12500\n"
    "staff__sha512_crypt__default_rounds = 100000\n"
    "superuser__django_pbkdf2_sha256__default_rounds = 15000\n"
    "superuser__sha512_crypt__default_rounds = 120000\n"
)
