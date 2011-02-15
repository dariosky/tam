# coding: utf-8
import os
from socket import gethostname

TAM_VERSION="2.0b"
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

host=gethostname().lower()
if host in ("dariosky", "acido"):
	DEBUG=True	# siamo in Test
else:
	DEBUG=False
#print "Debug:", DEBUG, host

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Dario Varotto', 'dario.varotto@gmail.com'),
)

MANAGERS = ADMINS
usaSqlite = True # Forzo ad usare il db in sqlite
if usaSqlite:
	DATABASES = {	# DB di produzione
		'default': {
				'ENGINE': 'django.db.backends.sqlite3',		# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
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
				'ENGINE': 'django.db.backends.postgresql_psycopg2',		# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
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

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, "media/")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '7@*a$hce=f6fhavob3i4lj*3h72wu73dw!trinyuz-87zqd^3e'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
	'tam.middleware.loginRequirement.RequireLoginMiddleware',
    'django.middleware.doc.XViewMiddleware',
	
    'django.middleware.transaction.TransactionMiddleware',

	'tam.middleware.threadlocals.ThreadLocals',
#	'tam.middleware.sqlLogMiddleware.SQLLogMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG={"INTERCEPT_REDIRECTS":False}

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
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',

    'tam',
	'south',
	'tamArchive',
	'license',
#    'debug_toolbar',
)

LOGIN_URL="/login/"
LOGIN_REDIRECT_URL="/"

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'info@dariosky.it'
EMAIL_HOST_PASSWORD = 'bangbangD'
EMAIL_PORT = 587

if DEBUG:
	import logging
	logging.basicConfig(
				level=logging.DEBUG,
				format='%(asctime)s %(levelname)s %(message)s'
			)

SESSION_COOKIE_AGE = 2*60*60	# cookie age in seconds (60 minutes)

LICENSE_OWNER = 'ARTE Taxi'
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