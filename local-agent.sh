#!/bin/sh
# version=$(git rev-parse HEAD)
# version=20b3d150853d0d936910699675316f25861c6c19
# docker run -it --rm \
#   -e IAM_ROLE \
#   ktruckenmiller/aws-cli \
#   ecr get-login --region=us-west-2 --no-include-email > boston.txt
# eval "$(cat boston.txt)"
# docker pull 601394826940.dkr.ecr.us-west-2.amazonaws.com/drone:agent-$version
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e DRONE_RPC_SECRET=Anw3BbuLxiXhPmrmVnzdmRKJ \
  -e DRONE_RPC_SERVER=https://drone.kloudcover.com \
  -e DRONE_RUNNER_CAPACITY=6 \
  -e DRONE_RUNNER_NAME=truckstop \
  -e IAM_ROLE \
  -e AWS_DEFAULT_REGION=us-west-2 \
  -e AWS_REGION=us-west-2 \
  -e DRONE_RUNNER_LABELS=instance:truckstop \
  drone/agent:1.2.3
