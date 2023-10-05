#!/bin/bash

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

set -e
TEST=${TEST:=false}
DJANGO_DEBUG=${DJANGO_DEBUG:=false}
MAKEMESSAGES=${MAKEMESSAGES:=true}
COMPILEMESSAGES=${COMPILEMESSAGES:=true}


if [ "$TEST" = true ]; then
  echo 'running tests'
  python manage.py test
fi
if [ "$DJANGO_DEBUG" = false ]; then
  echo 'collecting static files'
  ./manage.py collectstatic --no-input --clear
fi
if [ "$MAKEMESSAGES" = true ]; then
  echo 'making messages'
  python manage.py makemessages --all --no-obsolete --add-location file
fi
if [ "$COMPILEMESSAGES" = true ]; then
  echo 'compiling messages'
  python manage.py compilemessages
fi

exec "$@"
