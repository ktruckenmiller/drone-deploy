#!/bin/sh

set -e
VERSION="1.2.3"
REGION=${AWS_REGION:-'us-west-2'}
ACCOUNT=${AWS_ACCOUNT:-'601394826940'}

docker build -t $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/drone:agent-$VERSION -f Dockerfile.agent --build-arg VERSION=$VERSION .
docker build -t $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/drone:server-$VERSION -f Dockerfile.server --build-arg VERSION=$VERSION .

eval $(aws ecr get-login --no-include-email)

docker push 601394826940.dkr.ecr.us-west-2.amazonaws.com/drone:server-$VERSION
docker push 601394826940.dkr.ecr.us-west-2.amazonaws.com/drone:agent-$VERSION
