#!/bin/sh
set -e

echo "USER_MANAGEMENT: Applying database migrations..."
flask db upgrade

echo "USER_MANAGEMENT: Seeding initial data..."
# 👇 เปลี่ยนเป็นคำสั่ง seed ใหม่ของเรา
flask seed

echo "USER_MANAGEMENT: Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:5000 wsgi:app