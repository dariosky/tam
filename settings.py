# coding: utf-8
import os
import logging
from socket import gethostname

TAM_VERSION = "3.4"
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
	DATABASE_OPTIONS = {
	   "timeout": 20,	# Sqlite will wait some more
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


# List of callables that know how to import templates from various sources.
if not DEBUG:
	TEMPLATE_LOADERS = (
		( 'django.template.loaders.cached.Loader', 	( # cache template loaders
			'django.template.loaders.filesystem.Loader',
			'django.template.loaders.app_directories.Loader',
			)
		),
	)


MIDDLEWARE_CLASSES = (
	'mediagenerator.middleware.MediaMiddleware',
#	'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware', # check requests for csrf
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
	'tam.middleware.loginRequirement.RequireLoginMiddleware',
#    'django.middleware.doc.XViewMiddleware',	# currently useless?

    'django.middleware.transaction.TransactionMiddleware',

	'tam.middleware.threadlocals.ThreadLocals',
	# 'tam.middleware.sqlLogMiddleware.SQLLogMiddleware',
)

ROOT_URLCONF = 'urls'

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


LICENSE_OWNER = ''		# to be shown on the footer
DATI_CONSORZIO = """""" # to be printed on the invoices
OWNER_LOGO = 'fatture/logo.jpg'	# relative to media folder
INVOICES_FOOTERS = {} # a dictionary with <invoinces type>:<list of footers>

# MEDIA GENERATOR **********
MEDIA_DEV_MODE = DEBUG
DEV_MEDIA_URL = '/mediadev/'
PRODUCTION_MEDIA_URL = '/mediaprod/'
GLOBAL_MEDIA_DIRS = (os.path.join(os.path.dirname(__file__), 'media'),)
MEDIA_BUNDLES = (
	# CSS *************
	('tam.css', 'css/tam.css',),
	('tam-stealth.css', 'css/tam-stealth.css',),
	('fatturaHtml.css', 'css/fatture.css',),
	('tamUI.css',
		'jquery.ui/css/ui-lightness/jquery-ui-1.8.16.custom.css',
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
		'js/tam-common.js',
	),
	('tamCorse.js',
		'js/jquery.min.js', 'js/jquery.hotkeys.js',
		'jquery.ui/js/jquery-ui-1.8.16.custom.min.js', 'js/calendarPreferences.js',
		'js/tam-common.js', 'js/jquery.scrollTo-min.js', 'js/listaCorse.js',
	),
	('selFatture.js', 'js/fatture/table_selector.js'),
	('tamRules.css', 'css/tamrules.css'),
	('jquery.editable-1.3.3.js', 'js/jquery.editable-1.3.3.js'),
	('fattura.js', 'js/fatture/fattura.js'),
			
)
YUICOMPRESSOR_PATH = os.path.join(PROJECT_PATH, 'yuicompressor.jar')
if os.path.exists(YUICOMPRESSOR_PATH):
	ROOT_MEDIA_FILTERS = {
		'js': 'mediagenerator.filters.yuicompressor.YUICompressor',
		'css': 'mediagenerator.filters.yuicompressor.YUICompressor',
	}
# **************************

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
)


LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'info@dariosky.it'
EMAIL_HOST_PASSWORD = 'bangbangD'
EMAIL_PORT = 587

#if DEBUG:
#	logging.basicConfig(
#				level=logging.DEBUG,
#				format='%(asctime)s %(levelname)s %(message)s'
#			)

if DEBUG:
	SESSION_COOKIE_AGE = 60*60*24*14	# 14 giorni in debug
else:
	SESSION_COOKIE_AGE = 30 * 60	# cookie age in seconds (30 minutes)

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
if use_debug_toolbar :
	# put the debug toolbar middleware right after the Gzip middleware
	try:
		# middleware_split_position = MIDDLEWARE_CLASSES.index('django.middleware.gzip.GZipMiddleware') + 1
		middleware_split_position = 0 #  put the toolbar middleware at the start
		MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES[:middleware_split_position] + \
						('debug_toolbar.middleware.DebugToolbarMiddleware',) + \
						MIDDLEWARE_CLASSES
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

PASSWORD_HASHERS = (
	'django.contrib.auth.hashers.SHA1PasswordHasher',	# Still use the old hashing until I pass to 1.4
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

TAM_VIAGGI_PAGINA = 100

try:
	from settings_local import * #@UnusedWildImport
except ImportError:
	logging.warning("Local settings file 'settings_local.py' has not been found. Use this to out of VC secret settings.")
	pass