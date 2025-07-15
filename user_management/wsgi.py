import os
from app import create_app, socketio

config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    socketio.run(app)
