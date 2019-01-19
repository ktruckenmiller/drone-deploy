#!/bin/sh
export DRONE_RPC_SECRET=$(ssm_get_parameter /drone/SECRET)
# export DRONE_DEBUG=true
/bin/drone-agent
