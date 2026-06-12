#!/bin/sh

echo "Waiting for postgres..."
if [ "$DATABASE" = "postgres" ]
then
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
fi

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000