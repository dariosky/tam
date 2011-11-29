# coding: utf-8
import os
from socket import gethostname

TAM_VERSION = "2.1f"
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

host = gethostname().lower()
if host in ("dariosky", "acido"):
	DEBUG = True	# siamo in Test
else:
	DEBUG = False

#DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Dario Varotto', 'dario.varotto@gmail.com'),
)

MANAGERS = ADMINS
usaSqlite = True # Forzo ad usare il db in sqlite
if usaSqlite:
	DATABASES = {	# DB di produzione
		'default': {
				'ENGINE': 'django.db.backends.sqlite3', 		# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
				'NAME': os.path.join(PROJECT_PATH, 'tam.db3')
		},
		'archive': {
				'ENGINE': 'django.db.backends.sqlite3',
				'NAME': os.path.join(PROJECT_PATH, 'tamarchive.db3')
		}
	}
else:
	DATABASES = {	# DB di test
		'default': {
				'ENGINE': 'django.db.backends.postgresql_psycopg2', 		# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
				'NAME': 'tam',
				'USER': 'tam',
				'PASSWORD': 'tampg',
				'HOST':'localhost', 'PORT':5432
		},
		'archive': {
				'ENGINE': 'django.db.backends.postgresql_psycopg2',
				'NAME': 'tamArchive',
				'USER': 'tam',
				'PASSWORD': 'tampg',
				'HOST':'localhost', 'PORT':5432
		}
	}

DATABASE_ROUTERS = [ 'db_routers.TamArchiveRouter', ]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Rome'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'it-it'
USE_L10N = True
#USE_THOUSAND_SEPARATOR = True # mi incasina gli invii delle form

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True	# mi serve per le date

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, "media/")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

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
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)


# Make this unique, and don't share it with anybody.
SECRET_KEY = '7@*a$hce=f6fhavob3i4lj*3h72wu73dw!trinyuz-87zqd^3e'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
	'mediagenerator.middleware.MediaMiddleware',
#	'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware', # check requests for csrf
    'django.contrib.auth.middleware.AuthenticationMiddleware',
	'tam.middleware.loginRequirement.RequireLoginMiddleware',
#    'django.middleware.doc.XViewMiddleware',	# currently useless?

    'django.middleware.transaction.TransactionMiddleware',

	'tam.middleware.threadlocals.ThreadLocals',
	# 'tam.middleware.sqlLogMiddleware.SQLLogMiddleware',
)

ROOT_URLCONF = 'Tam.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)


TEMPLATE_CONTEXT_PROCESSORS = (
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	'django.core.context_processors.request',
	"django.contrib.messages.context_processors.messages",

	"license.context_processors.license_details",
	)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
#    'django.contrib.sites',
	'django.contrib.messages',
	'django.contrib.staticfiles',

    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
	'mediagenerator',

    'tam',
	'south',
	'tamArchive',

	'fatturazione',
#	'license',
#    'debug_toolbar',
)

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'info@dariosky.it'
EMAIL_HOST_PASSWORD = 'bangbangD'
EMAIL_PORT = 587

#if DEBUG:
#	import logging
#	logging.basicConfig(
#				level=logging.DEBUG,
#				format='%(asctime)s %(levelname)s %(message)s'
#			)

if DEBUG:
	SESSION_COOKIE_AGE = 60*60*24*14	# 14 giorni in debug
else:
	SESSION_COOKIE_AGE = 30 * 60	# cookie age in seconds (30 minutes)

LICENSE_OWNER = 'ARTE Taxi'
DATI_CONSORZIO = """ARTE Taxi
via P.Abano, 14
35031 Abano Terme (PD)
Partita IVA e CF: 01106280280
Tel: 049 667842 Fax: 049 667845
www.artetaxi.com  -  info@artetaxi.com"""

#import datetime
#LICENSE_EXPIRATION = datetime.date(2010, 01, 01)

# RabbitMQ info
rmquser = "tam"
rmqpass = "tamRMQ"
tmqhost = "tam"
""" To configure RMQ:
$ rabbitmqctl add_user tam tamRMQ
$ rabbitmqctl add_vhost tam
$ rabbitmqctl set_permissions -p tam tam ".*" ".*" ".*"
"""

#===============================================================================
# Set to True to use the debug_toolbar
use_debug_toolbar = DEBUG and False
if use_debug_toolbar:
	# put the debug toolbar middleware right after the Gzip middleware
	try:
		middleware_split_position = MIDDLEWARE_CLASSES.index('django.middleware.gzip.GZipMiddleware') + 1
		MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES[:middleware_split_position] + \
						('debug_toolbar.middleware.DebugToolbarMiddleware',) + \
						MIDDLEWARE_CLASSES[middleware_split_position:]
	except:
		pass
#	MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ('debug_toolbar.middleware.DebugToolbarMiddleware',)
	DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS":False}
	INTERNAL_IPS = ('127.0.0.1',)
	INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)
#===============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'TaM',
    }
}

# MEDIA GENERATOR **********

MEDIA_DEV_MODE = DEBUG
DEV_MEDIA_URL = '/mediadev/'
PRODUCTION_MEDIA_URL = '/mediaprod/'
GLOBAL_MEDIA_DIRS = (os.path.join(os.path.dirname(__file__), 'media'),)
MEDIA_BUNDLES = (
	# CSS *************
	('tam.css',
		'css/tam.css',
	),
	('tam-stealth.css',
		'css/tam-stealth.css',
	),
	('fatturaHtml.css',
		'css/fatture.css',
	),
	('tamUI.css',
		'jquery.ui/css/ui-lightness/jquery-ui-1.8.16.custom.css',
		'js/jquery-autocomplete/jquery.autocomplete.css',
		'css/tam.css',
	),
	# JS **************
	('tambase.js',
		'js/jquery.min.js', 'js/jquery.hotkeys.js',
		'js/tam-common.js',
	),
	('tamUI.js',
		'js/jquery.min.js', 'js/jquery.hotkeys.js',
		'jquery.ui/js/jquery-ui-1.8.16.custom.min.js', 'js/calendarPreferences.js',
		'js/jquery-autocomplete/jquery.autocomplete.min.js',
		'js/tam-common.js',
	),
	('tamCorse.js',
		'js/jquery.min.js', 'js/jquery.hotkeys.js',
		'jquery.ui/js/jquery-ui-1.8.16.custom.min.js', 'js/calendarPreferences.js',
		'js/jquery-autocomplete/jquery.autocomplete.min.js',		
		'js/tam-common.js', 'js/jquery.scrollTo-min.js', 'js/listaCorse.js', 'js/nuovaCorsaPag1.js'
	),
)
YUICOMPRESSOR_PATH = os.path.join(PROJECT_PATH, 'yuicompressor.jar')
if os.path.exists(YUICOMPRESSOR_PATH):
	ROOT_MEDIA_FILTERS = {
		'js': 'mediagenerator.filters.yuicompressor.YUICompressor',
		'css': 'mediagenerator.filters.yuicompressor.YUICompressor',
	}
# **************************
