#!/usr/bin/env python
import os
import subprocess
import uuid

# https://stackoverflow.com/questions/68527489/cant-import-migratecommand-from-flask-migrate
from flask_migrate import Migrate  # from flask_migrate import Migrate, MigrateCommand
import click
from flask import Flask, cli
from redis import Redis
from rq import Connection, Queue, Worker
from rq.exceptions import NoSuchJobError  # Import the exception
from app import create_app, db, socketio
from app.models import Role, User
from app.models.miscellaneous import EditableHTML
from config import Config

import logging

logging.basicConfig(level=logging.DEBUG)

# Check and print the environment variable
config_name = os.getenv('FLASK_CONFIG') or 'default'
logging.debug(f"Config name: {config_name}")

### os.environ['GEVENT_SUPPORT'] = 'True'

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# manager = Manager(app)
migrate = Migrate(app, db)


@app.context_processor
def inject_asset_path():
    return dict(asset_path=app.config['ASSET_PATH'])


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Role': Role, 'EditableHTML': EditableHTML}


@app.cli.command("test")
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command("recreate_db")
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@app.cli.command("add-fake-data")
@click.option('--number-users',
              default=10,
              help='Number of each model type to create')
def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)
    click.echo(f"Added {number_users} fake users.")


@app.cli.command()
def setup_dev():
    """Runs the set-up needed for local development."""
    print("Running setup_general...")
    setup_general()


@app.cli.command()
def setup_prod():
    """Runs the set-up needed for production."""
    print("Running setup_general...")
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""
    Role.insert_roles()
    admin_query = Role.query.filter_by(name='Administrator')
    if admin_query.first() is not None:
        if User.query.filter_by(email=Config.ADMIN_EMAIL).first() is None:
            uid = uuid.uuid4().hex
            user = User(first_name='Admin',
                        last_name='Account',
                        password=Config.ADMIN_PASSWORD,
                        confirmed=True,
                        email=Config.ADMIN_EMAIL,
                        uid=uid)
            db.session.add(user)
            db.session.commit()
            print('Added administrator {}'.format(user.full_name()))


@app.cli.command()
def run_worker():
    """Initializes a slim rq task queue."""
    listen = ['default']
    conn = Redis(host=app.config['RQ_DEFAULT_HOST'],
                 port=app.config['RQ_DEFAULT_PORT'],
                 db=0,
                 password=app.config['RQ_DEFAULT_PASSWORD'])

    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
        # สร้างคิวโดยใช้ connection ของ Redis
        queue = Queue(connection=conn)


@app.cli.command()
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print('Running {}'.format(isort))
    subprocess.call(isort, shell=True)

    print('Running {}'.format(yapf))
    subprocess.call(yapf, shell=True)


if __name__ == '__main__':
    # manager.run()
    # socketio.run(app, debug=True, port=5000)
    app.run(debug=True, port=5000)
