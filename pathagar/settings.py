
"""
This settings are for testing Pathagar with the Django development
server.  It will use a SQLite database in the current directory and
Pathagar will be available at http://127.0.0.1:8000 loopback address.

For production, you should use a proper web server to deploy Django,
serve static files, and setup a proper database.

"""


import os


# Books settings:

BOOKS_PER_PAGE = 20 # Number of books shown per page in the OPDS
                    # catalogs and in the HTML pages.
AUTHORS_PER_PAGE = 40 # Number of books shown per page in the OPDS
                      # catalogs and in the HTML pages.

BOOKS_STATICS_VIA_DJANGO = True
DEFAULT_BOOK_STATUS = 'Published'

# Allow non logued users to upload books
ALLOW_PUBLIC_ADD_BOOKS = False

# sendfile settings:

SENDFILE_BACKEND = 'sendfile.backends.development'

# Get current directory to get media and templates while developing:
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
# TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'database.db'),
    }
}

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'static_media')

MEDIA_URL = '/static_media/'

SECRET_KEY = '7ks@b7+gi^c4adff)6ka228#rd4f62v*g_dtmo*@i62k)qn=cs'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'pathagar.urls'

INTERNAL_IPS = ('127.0.0.1',)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

ALLOW_USER_COMMENTS = False

TAGGIT_CASE_INSENSITIVE = True

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'taggit',
    'django_comments',
    'books',
)


try:
    from local_settings import *
except ImportError:
    pass
