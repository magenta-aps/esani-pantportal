#!/bin/bash

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

set -e
MAKE_MIGRATIONS=${MAKE_MIGRATIONS:=false}
MIGRATE=${MIGRATE:=false}
DUMMYDATA=${DUMMYDATA:=false}
SKIP_IDP_METADATA=${SKIP_IDP_METADATA:=false}
TEST=${TEST:=false}
CREATE_GROUPS=${CREATE_GROUPS:=true}

if [ "$MAKE_MIGRATIONS" = true ] || [ "$MIGRATE" = true ]; then
  python3 manage.py wait_for_db
fi
if [ "$MAKE_MIGRATIONS" = true ]; then
  echo 'Generating migrations'
  python3 manage.py makemigrations --no-input
fi
if [ "$MIGRATE" = true ]; then
  echo 'Running migrations'
  python3 manage.py migrate
fi

echo "collecting static files"
python3 manage.py collectstatic --no-input --clear

if [ "${CREATE_GROUPS,,}" = true ]; then
  echo 'create groups'
  python manage.py create_groups
fi
if [ "$DUMMYDATA" = true ]; then
  echo 'Creating dummy data'
  python3 manage.py create_dummy_companies
  python3 manage.py create_dummy_users
  python3 manage.py create_dummy_products
  python3 manage.py create_dummy_objects_for_csv_import
  python3 manage.py create_dummy_refund_methods
fi

python manage.py createcachetable
if [ "$TEST" = true ]; then
  echo 'running tests'
  python manage.py test
fi

exec "$@"
