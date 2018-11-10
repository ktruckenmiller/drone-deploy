#!/bin/sh
export DRONE_RPC_SECRET=$(ssm_get_parameter /drone/SECRET)
export DRONE_GITHUB_CLIENT_ID=$(ssm_get_parameter /drone/GITHUB_CLIENT)
export DRONE_GITHUB_CLIENT_SECRET=$(ssm_get_parameter /drone/GITHUB_SECRET)
export DRONE_DATABASE_SECRET=$(ssm_get_parameter /drone/ENCRYPTION_PASSWORD)
export DRONE_DATABASE_DATASOURCE="drone:$(ssm_get_parameter /drone/RDS_PASSWORD)@tcp($(ssm_get_parameter /drone/RDS_HOST):3306)/drone?parseTime=true"
/bin/drone-server
