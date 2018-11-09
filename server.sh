#!/bin/sh
export DRONE_SECRET=$(ssm_get_parameter /drone/production/DRONE_DATABASE_DATASOURCE)
export DRONE_GITHUB_CLIENT=$(ssm_get_parameter /drone/production/DRONE_GITHUB_CLIENT)
export DRONE_GITHUB_SECRET=$(ssm_get_parameter /drone/production/DRONE_GITHUB_SECRET)
export DRONE_DATABASE_DATASOURCE=$(ssm_get_parameter /drone/production/DRONE_DATABASE_DATASOURCE)
/bin/drone-server
