#!/bin/sh

if [ "$DATABASE" = "mongodb" ]
then
    echo "Waiting for mongodb..."

    while ! nc -z $MONGO_HOST $MONGO_PORT; do
      sleep 0.1
    done

    echo "MongoDB started"
fi

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Start server
echo "Starting server"
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000
