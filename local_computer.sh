#!/bin/bash
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e DRONE_RUNNER_NAME=boston \
  -e IAM_ROLE=arn:aws:iam::601394826940:role/drone-TaskRole-16LQB3ZBMZQGE \
  -e AWS_REGION=us-east-1 \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e DRONE_RPC_SERVER=https://cicd.kloudcover.com \
  -e DRONE_RUNNER_LABELS=location:home \
  601394826940.dkr.ecr.us-east-1.amazonaws.com/drone:agent-e401fcdccb34aa32fae3ac1bc5b26fb9a08217ed
