# settings.py:
# Django settings for binalerts project.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

# Some special mysociety preamble in order to get hold of our config
# file conf/general
import os
import sys
package_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))

paths = (
    os.path.normpath(package_dir + "/../../pylib"),
    os.path.normpath(package_dir + "/../../commonlib/pylib"),
    os.path.normpath(package_dir + "/../../commonlib/pylib/djangoapps"),
)

for path in paths:
    if path not in sys.path:
        sys.path.append(path)

try:
    from config_local import config  # put settings in config_local if you're not running in a full mysociety vhost
    SERVE_STATIC_FILES = True
except ImportError:
    SERVE_STATIC_FILES = False
    from mysociety import config
    config.set_file(os.path.abspath(package_dir + "/../../conf/general"))


# Now follows the normal Django stuff.

DEBUG = config.get('DEBUG', False)
TEMPLATE_DEBUG = DEBUG

SERVER_EMAIL = config.get('BUGS_EMAIL')
ADMINS = (
    ('mySociety bugs', config.get('BUGS_EMAIL')),
)
DEFAULT_FROM_EMAIL = 'Bin Alerts <%s>' % config.get('BUGS_EMAIL')

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = config.get('BINS_DB_NAME')
DATABASE_USER = config.get('BINS_DB_USER')
DATABASE_PASSWORD = config.get('BINS_DB_PASS')
DATABASE_HOST = config.get('BINS_DB_HOST')
DATABASE_PORT = config.get('BINS_DB_PORT')

BINS_SITENAME = config.get('BINS_SITENAME')
DOMAIN_NAME = config.get('DOMAIN_NAME')

# True if the *same type of collection* can occur at a given address more than once a week
# (False may be common: e.g., recycling is only collected once a week)
# If false, it means if the a new collection day is read from the import, the old one will be deleted
BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK = config.get('BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK', True)

# It's a good idea to force all streets to have a postcode, to avoid ambiguity
# But just in case there's a place with no duplicate street names, allow it to be optional
BINS_STREETS_MUST_HAVE_POSTCODE = config.get('BINS_STREETS_MUST_HAVE_POSTCODE', True)

# Total number of days displayed on 'street' view: 
# probably should be a multiple of 7 since this is the number of days shown per row ("week") in default CSS
# 7 = one week (sensible for councils with weekly schedules)
# 14 = two weeks
BINS_DISPLAY_DAYS_SHOWN = config.get('BINS_DISPLAY_DAYS_SHOWN', 7)

# The day of the week the should be the first day displayed on 'street' view
# specify a day name ('Sunday') or 'today'
# For councils with a stricly weekly schedule, 'Sunday' makes some sense
BINS_DISPLAY_FIRST_DAY = config.get('BINS_DISPLAY_FIRST_DAY', 'Sunday')

# Should dates be displayed in street view? 
# False: no dates displayed (sensible for councils running weekly collections, i.e. 7-day cycles)
# True: dates displayed (councils on fortnightly collections)
BINS_DISPLAY_SHOW_DATES = config.get('BINS_DISPLAY_SHOW_DATES', False)

# Should bin collections be shown differently if they are in the past?
# False: no, display everything (sensible for councils running strictly weekly collections with no dates shown)
# True: yes, ghost past collections and don't stop the lorry at them
BINS_SHOW_PAST_DATES_DIFFERENTLY = config.get('BINS_SHOW_PAST_DATES_DIFFERENTLY', True)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-GB'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(package_dir, "../../web/static/")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('DJANGO_SECRET_KEY')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'djangoproj.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(package_dir, "binalerts/templates/" + BINS_SITENAME),
    os.path.join(package_dir, "binalerts/templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    #'django.contrib.gis',
    'djangoproj.binalerts',
    'emailconfirmation',
    'unsubscribe',
    'south'
)
