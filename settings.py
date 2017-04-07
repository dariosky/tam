# coding: utf-8
import hashlib
import os
import logging
from socket import gethostname

from utils.env_subs import perform_dict_substitutions

host = gethostname().lower()

TAM_VERSION = "6.81"
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
logger = logging.getLogger("tam.settings")

if 'TAM_DEBUG' in os.environ or 'webfaction' not in host:
    DEBUG = True
else:
    DEBUG = False
print("Running in %s MODE" % ("PRODUCTION" if not DEBUG else "DEBUG"))

# DEBUG = False

if DEBUG:
    # set naive Datetime as errors
    import warnings

    # warnings.simplefilter('error', DeprecationWarning)
    warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

ADMINS = (
    ('Dario Varotto', 'dario.varotto@gmail.com'),
)

MANAGERS = ADMINS
DATABASES = {}  # set them in settings_local

DATABASE_ROUTERS = [
    'db_routers.TamArchiveRouter',
    # 'modellog.db_routers.SeparateLogRouter'
]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Rome'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'it-it'
USE_L10N = True
# USE_THOUSAND_SEPARATOR = True # mi incasina gli invii delle form

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True  # mi serve per le date

# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(PROJECT_PATH, "media/")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)
STATICFILES_STORAGE = 'tam.storage.PipelineCachedStorage'

jqueryURL = 'js/jquery.min.js'  # 1.7.2, port no newer one should need change autocomplete
jqueryUIURL = 'js/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js'
jqueryUICSSURL = 'js/jquery-ui-1.10.3.custom/css/ui-lightness/jquery-ui-1.10.3.custom.min.css'

PIPELINE_CSS = {
    'tam': {'source_filenames': ['css/tam.css'],
            'output_filename': 'css/tam.min.css'},
    'tam-stealth': {'source_filenames': ['css/tam-stealth.css'],
                    'output_filename': 'css/tam-stealth.min.css'},
    'tamUI': {
        'source_filenames': (
            jqueryUICSSURL,
            'css/tam.css',
        ),
        'output_filename': 'css/tamUI.min.css',
    },
    'prenotazioni': {'source_filenames': ('css/prenotazioni.css',),
                     'output_filename': 'css/prenotazioni.min.css'},
    'codapresenze': {'source_filenames': ('css/codapresenze.css',),
                     'output_filename': 'css/codapresenze.min.css'},
}

PIPELINE_JS = {
    'tam': {
        'source_filenames': [jqueryURL, 'js/jquery.hotkeys.js',
                             'js/tam-common.js'],
        'output_filename': 'tam.min.js'
    },
    'tamUI': {
        'source_filenames': [jqueryURL, 'js/jquery.hotkeys.js',
                             jqueryUIURL, 'js/calendarPreferences.js',
                             'js/tam-common.js'],
        'output_filename': 'tamUI.min.js'
    },
    'tamCorse': {
        'source_filenames': [jqueryURL, 'js/jquery.hotkeys.js',
                             jqueryUIURL,
                             'js/calendarPreferences.js',
                             'js/tam-common.js',
                             'js/jquery.scrollTo-min.js', 'js/listaCorse.js'],
        'output_filename': 'tamCorse.min.js'
    },
    'jquery.editable': {
        'source_filenames': ['js/jquery.editable-1.3.3.js'],
        'output_filename': 'js/jquery.editable.min.js',
    },
    'fattura': {
        'source_filenames': ['fatturazione/fattura.js'],
        'output_filename': 'js/fattura.min.js',
    },
    'codapresenze': {
        'source_filenames': ['js/codapresenze.js'],
        'output_filename': 'js/codapresenze.min.js',
    },
}
PIPELINE_DISABLE_WRAPPER = True

PIPELINE_YUGLIFY_BINARY = os.path.join(PROJECT_PATH,
                                       'node_modules/.bin/yuglify')

# Pipeline 1.6 is still in early stages - here the settings
PIPELINE = dict(
    PIPELINE_ENABLED=True,
    STYLESHEETS={
        'tam': {'source_filenames': ['css/tam.css'],
                'output_filename': 'css/tam.min.css'},
        'tam-stealth': {'source_filenames': ['css/tam-stealth.css'],
                        'output_filename': 'css/tam-stealth.min.css'},
        'tamUI': {
            'source_filenames': (
                jqueryUICSSURL,
                'css/tam.css',
            ),
            'output_filename': 'css/tamUI.min.css',
        },
        'prenotazioni': {'source_filenames': ('css/prenotazioni.css',),
                         'output_filename': 'css/prenotazioni.min.css'},
        'codapresenze': {'source_filenames': ('css/codapresenze.css',),
                         'output_filename': 'css/codapresenze.min.css'},
    },
    JAVASCRIPT={
        'tam': {
            'source_filenames': [jqueryURL, 'js/jquery.hotkeys.js',
                                 'js/tam-common.js'],
            'output_filename': 'tam.min.js'
        },
        'tamUI': {
            'source_filenames': [jqueryURL, 'js/jquery.hotkeys.js',
                                 jqueryUIURL, 'js/calendarPreferences.js',
                                 'js/tam-common.js'],
            'output_filename': 'tamUI.min.js'
        },
        'tamCorse': {
            'source_filenames': [jqueryURL, 'js/jquery.hotkeys.js',
                                 jqueryUIURL,
                                 'js/calendarPreferences.js',
                                 'js/tam-common.js',
                                 'js/jquery.scrollTo-min.js', 'js/listaCorse.js'],
            'output_filename': 'tamCorse.min.js'
        },
        'jquery.editable': {
            'source_filenames': ['js/jquery.editable-1.3.3.js'],
            'output_filename': 'js/jquery.editable.min.js',
        },
        'fattura': {
            'source_filenames': ['fatturazione/fattura.js'],
            'output_filename': 'js/fattura.min.js',
        },
        'codapresenze': {
            'source_filenames': ['js/codapresenze.js'],
            'output_filename': 'js/codapresenze.min.js',
        },
    },
    DISABLE_WRAPPER=True,
    YUGLIFY_BINARY=os.path.join(PROJECT_PATH, 'node_modules/.bin/yuglify'),
    CSS_COMPRESSOR='pipeline.compressors.yuglify.YuglifyCompressor',
    JS_COMPRESSOR='pipeline.compressors.yuglify.YuglifyCompressor',
)

if not os.path.isdir(os.path.join(PROJECT_PATH, "logs")):
    os.mkdir(os.path.join(PROJECT_PATH, "logs"))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'formatters': {
        'main_formatter': {
            'format': '%(levelname)s:%(name)s: %(message)s '
                      '(%(asctime)s; %(filename)s:%(lineno)d)',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'main_formatter',
        },
        'production_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(PROJECT_PATH, 'logs', 'main.log'),
            'when': 'midnight',
            'utc': True,
            'delay': True,
            'backupCount': 7,
            'formatter': 'main_formatter',
            'filters': ['require_debug_false'],
        },
        'null': {
            "class": 'logging.NullHandler',
        }
    },
    'loggers': {
        'root': {
            'handlers': ['mail_admins', 'console'],
            'formatter': 'main_formatter',
            'level': 'ERROR',
            'propagate': True,
        },
        'django.server': {
            'level': 'WARNING'
        },
        'django.db': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
}

MIDDLEWARE_CLASSES = (
    # 'mediagenerator.middleware.MediaMiddleware',
    # 'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # check requests for csrf
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tam.middleware.loginRequirement.RequireLoginMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # 'django.middleware.transaction.TransactionMiddleware',
    #  deprecated in django 1.6

    'tam.middleware.threadlocals.ThreadLocals',
)

ROOT_URLCONF = 'urls'
CSRF_FAILURE_VIEW = 'tam.middleware.loginRequirement.csrf_failure_view'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',

                "license.context_processors.license_details",
                "tam.context_processors.common",
            ],
            'loaders': (
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ) if DEBUG else (
                ('django.template.loaders.cached.Loader', (
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                )),
            ),
        },
    },
]
LICENSE_OWNER = ''  # to be shown on the footer
DATI_CONSORZIO = """"""  # to be printed on the invoices
OWNER_LOGO = 'fatture/logo.jpg'  # relative to media folder
INVOICES_FOOTERS = {}  # a dictionary with <invoinces type>:<list of footers>

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',  # 'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.admindocs',
    'django.contrib.humanize',

    # this assetmanager is not more developed
    # and since django 1.2 it requires nothreading
    # 'mediagenerator',

    'pipeline',

    'tam',

    # it's no needed anymore in Django 1.7, thanks for serving us so well
    # 'south',

    'tamArchive',

    'fatturazione',

    'modellog',
    'securestore',
    # 'license',
    'tamhooks',

    'django.contrib.admin',
    'channels',
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

EMAIL_SUBJECT_PREFIX = "[TaM]"
MAIL_TAG = None

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days of session cookies

# import datetime
# LICENSE_EXPIRATION = datetime.date(2010, 01, 01)

# ===============================================================================
# Set to True to use the debug_toolbar
use_debug_toolbar = DEBUG and False
if use_debug_toolbar:
    DEBUG_TOOLBAR_CONFIG = {
        'JQUERY_URL': '',  # use the page jquery
    }
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        # 'template_timings_panel.panels.TemplateTimings.TemplateTimings',
    ]
    INSTALLED_APPS += [
        'debug_toolbar',
        # 'template_timings_panel'
    ]

if DEBUG:
    MIDDLEWARE_CLASSES += (
        # 'tam.middleware.profiler.ProfileMiddleware',
        # 'tam.middleware.sqlLogMiddleware.SQLLogMiddleware',
    )
# ===============================================================================

TAM_VIAGGI_PAGINA = 100

# ******************* CACHE
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'TaM',
    }
}

# we don't use session cookies (that doens't tamper the DB) cause we want
# to know what are the active session for the log
# SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

NOMI_DEFINIZIONE_FATTURE = ["FattureConsorzio", "FattureNoIVA",
                            "FattureConducente", "FattureConducenteNoIva",
                            "Ricevute"]
MIN_PRICE_FOR_TAXSTAMP = 77.47

SECURE_STORE_LOCATION = os.path.join(PROJECT_PATH, 'media_secured')
SECURE_STORE_CUSTOM_SUBFOLDER = None
SECURE_URL = "/secure/"

PLUGGABLE_APPS = {}

# Max numbers of rows allowed for XLS export
MAX_XLS_ROWS = 15 * 1000

TAM = dict(
    SPECIAL_FILTERS=dict(
        BUS=False,  # allow filter bus, for whatever driver name containing "bus"
    ),
)
TAM_BACKGROUND_COLOR = '#FBFFBA'  # the default background
TAM_SHOW_CLASSIFICA_FATTURE = False

FORCE_SINGLE_DEVICE_SESSION = False  # when true, the user cannot have multiple active sessions

GOOGLE_ANALYTICS_ID = None

# set password hasher, we use Argon as default
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}
     },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

RATELIMIT_CACHE_BACKEND = 'tam.ratelimit.RateCache'

# This are all settings for the deployment ***

PRENOTAZIONI_QUICK = dict(
    # choices=[dict(name="Locale"),  # no place_name means same place of client
    #          dict(name="Padova", place_name='.Padova Città'),
    #          dict(name="Venezia", place_name='.Venezia Marco Polo'),
    #          ],
    # defaults=dict(
    #     numero_passeggeri=2,
    #     note="Prenotazione rapida",
    #     esclusivo=True,
    # ),
)

WEBFACTION = {
    "APPS": dict(main='tam2beta',
                 redis='redis_tam',
                 media="tam2beta_media",
                 static="tam2beta_static"),
    "REDIS_PORT": 6379,
}
# This are all settings for the deployment ***
WEBHOST = "www.hostname.com"  # the main hostname serving the site
ALLOWED_HOSTS = [WEBHOST]
DEPLOYMENT = dict(  # defining parameters for the deployment
    NAME="TaM",  # the name of the process
    HOST="tam",  # the hostname, eventually you can use your .ssh/config
    REMOTE_SSH_PORT=22,

    USE_SUPERVISOR=False,
    SUPERVISOR_JOBNAME='tam',

    GIT_REPOSITORY="git@github.com:dariosky/tam.git",  # repository for clone
    WEBHOST=WEBHOST,

    FOLDERS=dict(
        HOME='/home/user',
        REPOSITORY_FOLDER="{HOME}/repo/tam",
        VENV_FOLDER="{HOME}/.environments/tam",
        REQUIREMENT_PATH="{REPOSITORY_FOLDER}/requirements/requirements.txt",
        STATIC_FOLDER="{REPOSITORY_FOLDER}/static",  # static assets collected
        MEDIA_FOLDER="{REPOSITORY_FOLDER}/media",  # This is for UGC
        LOGDIR="{REPOSITORY_FOLDER}/logs",
    ),

    FRONTEND=dict(
        RUN_COMMAND="{REPOSITORY_FOLDER}/manage.py daphne start",
        PORT=8888,
        PID_FILE="{LOGDIR}/pids/daphne.pid",
        LOG_FILE="{LOGDIR}/daphne.log",
    ),

    WORKERS=dict(
        THREADS=4,
        PID_FILE="{LOGDIR}/pids/workers.pid",
        LOG_FILE="{LOGDIR}/workers.log",
    ),

    WSGI_APPLICATION="wsgi:application",
    BRAND_FOLDER="brand",  # this is a subfolder, per deployment of static brand assets
)
# WARNING: set a new password here
REDIS_PASSWORD = ""  # example: hashlib.sha256(b"a secure password").hexdigest()
REDIS_DATABASE = 0
REDIS_URL = 'redis://:{password}@{host}:{port}/{db}'.format(
    password=REDIS_PASSWORD,
    host='localhost',
    port=WEBFACTION['REDIS_PORT'],
    db=REDIS_DATABASE,
)

# END OF DEFAULTS **************************************************************

settings_file = os.environ.get('TAM_SETTINGS', 'settings_local')
try:
    # Dynamically import settings from the specified sys envoronment var
    # from settings_local import *
    print("TAM using {}".format(settings_file))
    localsets = __import__(settings_file, globals(), locals(), ['*'])
    for k in dir(localsets):
        locals()[k] = getattr(localsets, k)
except ImportError:
    logging.warning("'%s.py' has not been found." % settings_file +
                    "Use this to keep out of VC secret settings.")
    pass

for app, desc in PLUGGABLE_APPS.items():
    INSTALLED_APPS.append(app)

WSGI_APPLICATION = 'wsgi.application'

CHANNEL_LAYERS = dict(
    default=dict(
        BACKEND="asgi_redis.RedisChannelLayer",
        CONFIG={
            'hosts': [os.environ.get('REDIS_URL', REDIS_URL)],
        },
        ROUTING="routing.channel_routing",
    )
)

perform_dict_substitutions(DEPLOYMENT)  # change the deployment string to use a kind of templates
