#!/bin/sh
export DRONE_SECRET=$(ssm_get_parameter /drone/production/DRONE_DATABASE_DATASOURCE)
export DRONE_DEBUG=true
/bin/drone-agent
