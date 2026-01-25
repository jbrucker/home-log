#!/bin/bash
# Command to dump the schema of a Postgres database.
# Add  `-f filename` to direct the output to a file.

echo "Password is ${POSTGRES_PASSWORD}"
echo ${POSTGRES_PASSWORD} | pg_dump -d $POSTGRES_DB -U $POSTGRES_USER -W --schema-only 
