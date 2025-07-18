#!/usr/bin/env python
# user_management/manage.py
import os
import subprocess
import uuid

# https://stackoverflow.com/questions/68527489/cant-import-migratecommand-from-flask-migrate
from flask_migrate import Migrate  # from flask_migrate import Migrate, MigrateCommand
import click
from flask import Flask, cli
from flask.cli import with_appcontext
from redis import Redis
from rq import Connection, Queue, Worker
from rq.exceptions import NoSuchJobError  # Import the exception
from app import create_app, db, socketio
from app.models import Role, User
from app.models.miscellaneous import EditableHTML
from config import Config
from app.apicall import register_api_key_from_script

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

@app.cli.command("seed")
@with_appcontext  # 👈 เพิ่ม decorator นี้เข้าไป
def seed():
    """Seeds the database with initial data and syncs with other services via API."""
    
    print("--- 1. Seeding user_management database ---")
    
    Role.insert_roles()
    print("Roles inserted successfully.")

    admin_user = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
    if not admin_user:
        admin_role = Role.query.filter_by(name='Administrator').first()
        if admin_role:
            uid = uuid.uuid4().hex
            admin_user = User(
                first_name='Admin',
                last_name='Account',
                password=app.config['ADMIN_PASSWORD'],
                confirmed=True,
                email=app.config['ADMIN_EMAIL'],
                role=admin_role,
                uid=uid
            )
            db.session.add(admin_user)
            # db.session.commit()
            print(f"Admin user '{admin_user.email}' created successfully.")
        else:
            print("Error: Administrator role not found.")
            return
    else:
        print("Admin user already exists.")

    # --- สร้างข้อมูลเริ่มต้นสำหรับหน้า About ---
    print("Seeding initial 'about' page content...")
    if EditableHTML.query.filter_by(editor_name='about').first() is None:
        # ใช้ triple quotes (""") เพื่อครอบ HTML ที่มีหลายบรรทัด
        about_content = """<h3>Introduction</h3>
        <p>The URL Shortener project is a versatile tool designed to convert long URLs into shorter, more manageable links. It aims to provide users with a seamless experience in managing and sharing URLs, whether for personal use or business needs. The project emphasizes simplicity, security, and efficiency, making it an ideal solution for anyone looking to streamline their online presence.</p>
        <h3>Features</h3>
        <ol>
            <li><strong>URL Shortening</strong>: Converts long URLs into short, easy-to-share links.</li>
            <li><strong>QR Code Generation</strong>: Generates QR codes for shortened URLs, which can be displayed on the screen or downloaded as base64 images.</li>
            <li><strong>API Access</strong>: Provides a <a href="https://url.nt.th/docs" target="_blank">FastAPI-based API</a> for programmatic access to URL shortening features.</li>
            <li><strong>URL Safety Check:</strong> Automatically checks the destination URL for security risks, such as malware or phishing, and warns users to ensure safe access through the short URL.</li>
        </ol>
        <h3>Funding</h3>
        <p>This project received funding from National Telecom in 2024, which has been instrumental in supporting its development and implementation.</p>
        <p><strong>Contact Us</strong></p>
        <p>If you have any questions, feedback, or need assistance with the URL Shortener project, our team is here to help. Feel free to reach out to us through our support channels. We are committed to providing you with the best experience and ensuring your needs are met.</p>
        <p>For more information, please visit our support page or contact us directly at kaebmoo@gmail.com.&nbsp;</p>
        <p>We're looking forward to hearing from you!</p>
        <p>&nbsp;</p>"""
        
        about_page = EditableHTML(
            editor_name='about',
            value=about_content
        )
        db.session.add(about_page)
        print("'About' page content seeded.")
    else:
        print("'About' page content already exists.")

    # --- Commit การเปลี่ยนแปลงทั้งหมด ---
    try:
        db.session.commit()
        print("User DB commit successful.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred during 'user' db commit: {e}")
        return

    if admin_user:
        print(f"--- 2. Syncing admin API key to shortener_app ---")
        try:
            # ตอนนี้โค้ดข้างใน apicall.py จะสามารถเข้าถึง current_app.config ได้แล้ว
            result, status_code = register_api_key_from_script(admin_user.uid, admin_user.role_id)
            print(f"API call to register key result: {result} (Status: {status_code})")
        except Exception as e:
            print(f"An error occurred while calling register_api_key API: {e}")
    

    print("--- Seeding process finished ---")

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
