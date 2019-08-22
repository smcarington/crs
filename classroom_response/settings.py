"""
Django settings for classroom_response project.

Generated by 'django-admin startproject' using Django 1.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os,socket,math,random,fractions

from simpleeval import simple_eval, NameNotDefined

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADMINS = [('Tyler', 'tyler.holden@utoronto.ca')]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1f@)#j@ruuv&azgoqlkav86^$&p4*d3i77x$zx2e#e!@w#k10#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    'guardian',
    'channels',
    'accounts',
    'quizzes',
    'polls',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'polls.middleware.UtorAuthMiddleware.UtorAuthMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.RemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

SHIBBOLETH_ATTRIBUTE_MAP = {
    "utorid": (True, "username"),
}

ROOT_URLCONF = 'classroom_response.urls'

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
        },
    },
]

WSGI_APPLICATION = 'classroom_response.wsgi.application'
# For channels to work
ASGI_APPLICATION = "classroom_response.routing.application"


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Toronto'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

# Project Specific Settings
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

URL_PREPEND = ''
WS_PREPEND = URL_PREPEND
SITE_NAME = ''
SITE_URL = ''
NOTES_URL = ''
NOTE_ROOT = '/tmp/'
MEDIA_URL  = '/media/'
LATEX_ROOT = '/home/tholden/djangotest/latex'
LOG_ROOT = '/tmp'
MARKS_LOG = "/".join([LOG_ROOT, 'marks_log.log'])
SENDFILE_BACKEND = 'sendfile.backends.development'

# For websockets we need to define the CHANNEL_LAYERS setting

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        #"BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [('127.0.0.1', 6379)], #[os.environ.get('REDIS_URL', 'redis://localhost:6379')],
        },
        #"ROUTING": "polls.routing.channel_routing",
    },
}

UNIVERSAL_CONSTANTS =  {"pi": math.pi, "e": math.e}
PREDEFINED_FUNCTIONS = {"sin": lambda x: math.sin(x),
                        "cos": lambda x: math.cos(x),
                        "tan": lambda x: math.tan(x),
                        "ln": lambda x: math.log(x, math.e),
                        "rand": lambda x,y: random.randint(x,y),
                        "Rand": lambda x,y: NZRandInt(x,y),
                        "uni": lambda x,y,z: round(random.uniform(x,y),z),
                        "gobble": lambda *args: 1,
                        "abs": lambda x: abs(x),
                        "max": lambda *args: max(*args),
                        "min": lambda *args: min(*args),
                        "redfrac": lambda x,y: reduced_fraction(x,y),
                        }

def NZRandInt(x,y):
    """ Generates a random non-zero number between x and y """
    if x>0: # Behave like normal if x>0
        return random.randint(x,y)
    else:
        if random.randint(0,1):
            return random.randint(x,-1)
        else:
            return random.randint(1,y)

def reduced_fraction(num, den):
    """ Given a fraction num/den where num/den are strings, produces the LaTeX
        string for the reduced fraction. For example,
        reduced_fraction(3,9) = \frac{{1}}{{3}} while
        reduced_fraction(4,2) = 2
        <<INPUT>> 
        num, den (strings) for the numerator and denominator
    """
    template="{}\\frac{{ {} }}{{ {} }}"
    sign = ''
    try:
        numer = int(simple_eval(str(num)))
        denom = int(simple_eval(str(den)))

        if not denom:
            raise TypeError('Denominator cannot be zero or empty')

        gcd = fractions.gcd(numer, denom)
        (red_num, red_den) = (numer/gcd, denom/gcd)

        if red_den == 1:
            return str(int(red_num))
        else:
            if red_num*red_den < 0:
                sign = '-'
            return template.format(sign, int(abs(red_num)), int(abs(red_den)))

    except TypeError as e:
        raise e

#
# Get local settings
try:
    from .local_settings import *
except ImportError as e:
    print('No local settings detected')

