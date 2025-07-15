import os
import sys

from raygun4py.middleware import flask as flask_raygun

PYTHON_VERSION = sys.version_info[0]
if PYTHON_VERSION == 3:
    import urllib.parse
else:
    import urlparse

basedir = os.path.abspath(os.path.dirname(__file__))
config_file = os.path.join(basedir, 'config.env')
if os.path.exists(config_file):
    print('Importing environment from config.env file')
    for line in open(config_file):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1].replace("\"", "")


class Config:
    APP_NAME = os.environ.get('APP_NAME', 'Flask-Base')
    if os.environ.get('SECRET_KEY'):
        SECRET_KEY = os.environ.get('SECRET_KEY')
    else:
        SECRET_KEY = 'SECRET_KEY_ENV_VAR_NOT_SET'
        print('SECRET KEY ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # FastAPI
    SHORTENER_HOST = os.environ.get('SHORTENER_HOST', 'http://127.0.0.1:8000')

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.sendgrid.net')
    MAIL_PORT = os.environ.get('MAIL_PORT', 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    # EMAIL_SENDER=os.environ.get('EMAIL_SENDER')

    # Analytics
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')
    SEGMENT_API_KEY = os.environ.get('SEGMENT_API_KEY', '')

    # Admin account
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'kaebmoo@gmail.com')
    EMAIL_SUBJECT_PREFIX = '[{}]'.format(APP_NAME)
    EMAIL_SENDER = '{app_name} Admin <{email}>'.format(
        app_name=APP_NAME, email=os.environ.get('EMAIL_SENDER'))
    # MAIL_USERNAME can't use
    # use EMAIL_SENDER for sendgrid. Verify ownership of a single email address to use as a sender.

    # INFOBIP
    INFOBIP = os.environ.get('INFOBIP')
    NT_SMS_HOST = os.environ.get('NT_SMS_HOST')
    NT_SMS_API = os.environ.get('NT_SMS_API')
    NT_SMS_USER = os.environ.get('NT_SMS_USER')
    NT_SMS_PASS = os.environ.get('NT_SMS_PASS')
    NT_SMS_SENDER = os.environ.get('NT_SMS_SENDER')

    TIMEZONE = os.getenv('TIMEZONE', 'UTC')  # Default to UTC if not set
    APP_PATH = os.getenv(
        'APP_PATH', '/')  # กรณีกำหนด path อื่น เช่น /apps การทำ reverse proxy
    APP_HOST = os.getenv('APP_HOST',
                         'http://localhost')  # กำหนดเป็นชื่อ domain
    SHORTENER_HOST_NAME = os.getenv('SHORTENER_HOST_NAME', 'http://localhost')
    ASSET_PATH = os.getenv('ASSET_PATH', '')

    REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://127.0.0.1:6379')

    RAYGUN_APIKEY = os.environ.get('RAYGUN_APIKEY')

    # Parse the REDIS_URL to set RQ config variables
    if PYTHON_VERSION == 3:
        urllib.parse.uses_netloc.append('redis')
        url = urllib.parse.urlparse(REDIS_URL)
    else:
        urlparse.uses_netloc.append('redis')
        url = urlparse.urlparse(REDIS_URL)

    RQ_DEFAULT_HOST = url.hostname
    RQ_DEFAULT_PORT = url.port
    RQ_DEFAULT_PASSWORD = url.password
    RQ_DEFAULT_DB = 0

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DEV_DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite'))
    SQLALCHEMY_BINDS = {
        'blacklist_db':
        os.environ.get('DEV_BLACKLIST_DATABASE_URL',
                       'sqlite:///' + os.path.join(basedir, 'blacklist.db'))
    }

    @classmethod
    def init_app(cls, app):
        print('THIS APP IS IN DEBUG MODE. \
                YOU SHOULD NOT SEE THIS IN PRODUCTION.')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite'))
    SQLALCHEMY_BINDS = {
        'blacklist_db':
        os.environ.get('TEST_BLACKLIST_DATABASE_URL',
                       'sqlite:///' + os.path.join(basedir, 'blacklist.db'))
    }
    WTF_CSRF_ENABLED = False

    @classmethod
    def init_app(cls, app):
        print('THIS APP IS IN TESTING MODE.  \
                YOU SHOULD NOT SEE THIS IN PRODUCTION.')


class ProductionConfig(Config):
    DEBUG = False
    USE_RELOADER = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'user_management.sqlite'))
    SQLALCHEMY_BINDS = {
        'blacklist_db':
        os.environ.get('BLACKLIST_DATABASE_URL',
                       'sqlite:///' + os.path.join(basedir, 'blacklist.db'))
    }
    SSL_DISABLE = (os.environ.get('SSL_DISABLE', 'True') == 'True')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        assert os.environ.get('SECRET_KEY'), 'SECRET_KEY IS NOT SET!'

        flask_raygun.Provider(app, app.config['RAYGUN_APIKEY']).attach()


class HerokuConfig(ProductionConfig):

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # Handle proxy server headers
        # from werkzeug.contrib.fixers import ProxyFix
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)


class UnixConfig(ProductionConfig):

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig
}
