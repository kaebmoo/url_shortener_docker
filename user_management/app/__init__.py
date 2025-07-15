import os

from flask import Flask
from flask_assets import Environment
from flask_compress import Compress
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
# from flask_rq import RQ
from flask_rq2 import RQ
from rq import Queue
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_sse import sse

from app.assets import app_css, app_js, vendor_css, vendor_js
from config import config as Config

basedir = os.path.abspath(os.path.dirname(__file__))

mail = Mail()
db = SQLAlchemy()
csrf = CSRFProtect()
compress = Compress()
rq = RQ()
migrate = Migrate()
socketio = SocketIO()  # Initialize SocketIO

# Set up Flask-Login
login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'account.login'

def create_app(config):
    app = Flask(__name__, static_url_path='/static', static_folder='static')
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config['APPLICATION_ROOT'] = '/'
    # app.config['ASSET_URL'] = 'static'

    app.config["REDIS_URL"] = "redis://127.0.0.1"
    app.register_blueprint(sse, url_prefix='/stream')

    # Allow CORS for specific routes
    CORS(app, resources={r"/stream/*": {"origins": "*"}})

    # หากมีการใช้ header เฉพาะ (เช่น Authorization หรือ Custom Headers) คุณสามารถกำหนดได้ด้วย:
    # CORS(app, resources={r"/stream/*": {"origins": "*"}}, supports_credentials=True)
    
    config_name = config

    if not isinstance(config, str):
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app.config.from_object(Config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # not using sqlalchemy event system, hence disabling it

    Config[config_name].init_app(app)

    # Set up extensions
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    compress.init_app(app)
    migrate.init_app(app, db)  # อย่าลืมเรียกใช้ migrate.init_app
    
    # socketio = SocketIO(app)
    # socketio.init_app(app)
    # socketio.init_app(app, async_mode='gevent')  # eventlet

    rq.init_app(app)


    # Register Jinja template functions
    from .utils import register_template_utils
    register_template_utils(app)

    # Set up asset pipeline
    assets_env = Environment(app)
    dirs = ['assets/styles', 'assets/scripts']
    for path in dirs:
        assets_env.append_path(os.path.join(basedir, path))
    assets_env.url_expire = True

    assets_env.register('app_css', app_css)
    assets_env.register('app_js', app_js)
    assets_env.register('vendor_css', vendor_css)
    assets_env.register('vendor_js', vendor_js)


    # Configure SSL if platform supports it
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        SSLify(app)

    # Create app blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .account import account as account_blueprint
    app.register_blueprint(account_blueprint, url_prefix='/account')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .url import shorten as shorten_blueprint
    app.register_blueprint(shorten_blueprint, url_prefix='/url')

    # Add socketio to app context
    # app.socketio = socketio

    return app
