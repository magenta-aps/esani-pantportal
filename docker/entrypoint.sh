#!/bin/bash

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

set -e
MAKE_MIGRATIONS=${MAKE_MIGRATIONS:=false}
MIGRATE=${MIGRATE:=false}
DUMMYDATA=${DUMMYDATA:=false}
SKIP_IDP_METADATA=${SKIP_IDP_METADATA:=false}

if [ "$MAKE_MIGRATIONS" = true ] || [ "$MIGRATE" = true ]; then
  python3 manage.py wait_for_db
  if [ "$MAKE_MIGRATIONS" = true ]; then
    echo 'Generating migrations'
    python3 manage.py makemigrations
  fi
  if [ "$MIGRATE" = true ]; then
    echo 'Running migrations'
    python3 manage.py migrate
  fi
  if [ "$DUMMYDATA" = true ]; then
      echo 'Creating dummy data'
      python3 manage.py create_dummy_companies
      python3 manage.py create_dummy_products
      python3 manage.py create_dummy_packagingregistrations
  fi
fi

python manage.py createcachetable
if [ "$SKIP_IDP_METADATA" = false ]; then
  python manage.py update_mitid_idp_metadata
fi

exec "$@"
