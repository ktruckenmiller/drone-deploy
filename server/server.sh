#!/bin/sh
export DRONE_DATABASE_DATASOURCE="drone:$RDS_PASSWORD@tcp($RDS_HOST:3306)/drone-1.0?parseTime=true"
/bin/drone-server
