#!/bin/bash

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

set -e

GENERATE_DB_DOCUMENTATION=${GENERATE_DB_DOCUMENTATION:=true}
if [[ "${GENERATE_DB_DOCUMENTATION,,}" = true ]]; then
  echo 'Generating DB Documentation'

  DATABASE_READY=false
  echo $DATABASE_READY > /tmp/DATABASE_READY

  # Wait for database to come online
  while [[ $DATABASE_READY != true ]] ; do
    DATABASE_READY=`cat /tmp/DATABASE_READY`
    sleep 1
  done

  java -jar /usr/local/share/schemaspy.jar -dp /usr/local/share/postgresql.jar -t pgsql -db $POSTGRES_DB -host $POSTGRES_HOST -u $POSTGRES_USER -p $POSTGRES_PASSWORD -o /doc

  # Signal that the documentation is now ready
  echo true > /tmp/DOCUMENTATION_READY

  exec "$@"

fi
