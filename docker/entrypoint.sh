#!/bin/bash
set -e
MAKE_MIGRATIONS=${MAKE_MIGRATIONS:=false}
MIGRATE=${MIGRATE:=false}

if [ "$MAKE_MIGRATIONS" = true ] || [ "$MIGRATE" = true ]; then
  python3 manage.py wait_for_db
  if [ "$MAKE_MIGRATIONS" = true ]; then
    echo 'generating migrations'
    python3 manage.py makemigrations
  fi
  if [ "$MIGRATE" = true ]; then
    echo 'running migrations'
    python3 manage.py migrate
  fi
fi
exec "$@"
