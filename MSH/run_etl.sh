#!/bin/bash
. $MSH/initialize_environment_vars.sh
source activate python3

common_libs=$MSH/../common_libs

# create DB schemas
$common_libs/bin/psqlwrapper.sh $MSH/etl/SchemaSetup.sql

# load data
python load_data.py

# transforms
$common_libs/bin/psqlwrapper.sh $MSH/etl/transform/001_clean_customer_attributes.sql
$common_libs/bin/psqlwrapper.sh $MSH/etl/transform/002_remove_outliers.sql
