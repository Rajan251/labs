#!/bin/sh

if [ "$DATABASE" = "mongodb" ]
then
    echo "Waiting for mongodb..."

    while ! nc -z $MONGO_HOST $MONGO_PORT; do
      sleep 0.1
    done

    echo "MongoDB started"
fi

# Start server
echo "Starting server"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
