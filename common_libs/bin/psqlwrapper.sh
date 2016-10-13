#!/bin/bash

set -e
set -u

if [ $# != 1 ]; then
    echo "please enter the path to a sql file"
    exit 1
fi

export SQLFILE=$1

psql \
    -X \
    -U ec2_user \
    -h $PGHOSTNAME \
    -f $SQLFILE \
    --echo-all \
    --set AUTOCOMMIT=off \
    --set ON_ERROR_STOP=on \
    postgres

psql_exit_status=$?

if [ $psql_exit_status != 0 ]; then
    echo "psql failed while trying to run this sql script" 1>&2
    exit $psql_exit_status
fi

echo "sql script successful"
exit 0
