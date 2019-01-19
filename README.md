## Drone on ECS

A deployment for Drone CI on ECS

#### Prerequisites


1. Docker for Mac/Windows
1. ECS Cluster - [create](https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/clusters/create/new)
1. [Docker Friend](https://github.com/ktruckenmiller/docker-friend) or inline your aws directory into the `Makefile` docker run
1. Put secrets into SSM

#### Things this creates

1. RDS
1. Drone
