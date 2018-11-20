# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# Django settings for the AiiDA project.
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import sys
import os

from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.common.exceptions import ConfigurationError, MissingConfigurationError

# get_property is used to read properties stored in the config json
from aiida.common.setup import (get_config, get_secret_key, get_property,
                                get_profile_config, parse_repository_uri)
from aiida.backends import settings
from aiida.utils.timezone import get_current_timezone

# Assumes that parent directory of aiida is root for
# things like templates/, SQL/ etc.  If not, change what follows...


AIIDA_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.split(AIIDA_DIR)[0]
sys.path = [BASE_DIR] + sys.path

try:
    confs = get_config()
except MissingConfigurationError:
    raise MissingConfigurationError(
        "Please run the AiiDA Installation, no config found")

if settings.AIIDADB_PROFILE is None:
    raise ConfigurationError(
        "settings.AIIDADB_PROFILE not defined, did you load django"
        "through the AiiDA load_dbenv()?")

PROFILE_CONF = get_profile_config(settings.AIIDADB_PROFILE, conf_dict=confs)

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', or 'oracle'.
        'ENGINE': 'django.db.backends.' + PROFILE_CONF.get('AIIDADB_ENGINE', ''),
        'NAME': PROFILE_CONF.get('AIIDADB_NAME', ''),
        'USER': PROFILE_CONF.get('AIIDADB_USER', ''),
        'PASSWORD': PROFILE_CONF.get('AIIDADB_PASS', ''),
        'HOST': PROFILE_CONF.get('AIIDADB_HOST', ''),
        'PORT': PROFILE_CONF.get('AIIDADB_PORT', ''),
    }
}

# Checks on the REPOSITORY_* variables
try:
    REPOSITORY_URI = PROFILE_CONF['AIIDADB_REPOSITORY_URI']
except KeyError:
    raise ConfigurationError(
        "Please setup correctly the REPOSITORY_URI variable to "
        "a suitable directory on which you have write permissions.")

# Note: this variable might disappear in the future
REPOSITORY_PROTOCOL, REPOSITORY_PATH = parse_repository_uri(REPOSITORY_URI)

if settings.IN_RT_DOC_MODE:
    pass
elif REPOSITORY_PROTOCOL == 'file':
    # Note: to verify whether this is too slow to do at every startup
    if not os.path.isdir(REPOSITORY_PATH):
        try:
            # Try to create the local repository folders with needed parent
            # folders
            os.makedirs(REPOSITORY_PATH)
        except OSError:
            # Possibly here due to permission problems
            raise ConfigurationError(
                "Please setup correctly the REPOSITORY_PATH variable to "
                "a suitable directory on which you have write permissions. "
                "(I was not able to create the directory.)")
else:
    raise ConfigurationError("Only file protocol supported")

# CUSTOM USER CLASS
AUTH_USER_MODEL = 'db.DbUser'

# Make this unique, and don't share it with anybody.
# This is generated with the first run of 'verdi install'
SECRET_KEY = get_secret_key()

# Automatic logging configuration for Django is disabled here
# and done for all backends in aiida/__init__.py
LOGGING_CONFIG = None

###################################################
### keep (almost) default django conf below #######
###################################################

# Keep DEBUG = False! Otherwise every query is stored in memory
DEBUG = False

ADMINS = []
ALLOWED_HOSTS = []

MANAGERS = ADMINS

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# Local time zone for this installation. Always choose the system timezone
TIME_ZONE = get_current_timezone().zone


SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
# For AiiDA, leave it as True, otherwise setting properties with dates will not work.
USE_TZ = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'aiida.backends.djsite.settings.wsgi.application'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'aiida.backends.djsite.db',
    'aldjemy',
]

ALDJEMY_DATA_TYPES = {
    'UUIDField': lambda field: UUID(),
    'JSONField': lambda field: JSONB(),
}
