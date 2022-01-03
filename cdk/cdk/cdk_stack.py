from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as alb,
    aws_route53 as route53,
    aws_ssm as ssm,
    aws_logs as logs,
    aws_iam as iam,
    aws_certificatemanager as certy,
    Fn,
)
from aws_cdk.aws_ecr_assets import DockerImageAsset
from constructs import Construct


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.host_name = "drone.kloudcover.com"
        self.s3_bucket = s3.Bucket.from_bucket_arn(
            self,
            "S3Bucket",
            bucket_arn="arn:aws:s3:::drone-logs-us-west-2-601394826940",
        )
        self.vpc = ec2.Vpc.from_lookup(
            self,
            "Vpc",
            vpc_id="vpc-849531e0",
        )
        self.load_balancer = alb.ApplicationLoadBalancer.from_application_load_balancer_attributes(
            self,
            "alb",
            load_balancer_arn="arn:aws:elasticloadbalancing:us-west-2:601394826940:loadbalancer/app/kloudco-ALB-1XOWGRS4DIG1S/0d27cd3e97e641d1",
            vpc=self.vpc,
            security_group_id="sg-006232154f20712d1",
            load_balancer_dns_name="kloudco-ALB-1XOWGRS4DIG1S-1468524797.us-west-2.elb.amazonaws.com",
            load_balancer_canonical_hosted_zone_id="Z1IJC8V5Z715J8",
        )
        self.hosted_zone = route53.HostedZone.from_lookup(
            self, "hz", domain_name="kloudcover.com"
        )
        self.drone_secret_shared = self.get_ecs_secret("/drone/SECRET")
        self.cluster = ecs.Cluster.from_cluster_attributes(
            self,
            "cluster",
            cluster_name="production-kloudcover-v3",
            security_groups=[
                ec2.SecurityGroup.from_security_group_id(
                    self, "sg1", "sg-00ed611dc2f10830e"
                ),
                ec2.SecurityGroup.from_security_group_id(
                    self, "sg2", "sg-06604dd9d4fa8d6f5"
                ),
            ],
            vpc=self.vpc,
        )
        self.get_application()
        # self.get_autoscaler()

    def get_autoscaler(self):
        task_def = ecs.Ec2TaskDefinition(
            self,
            "TaskDefAutoscaler",
        )
        autoscaler_sg = ec2.SecurityGroup(
            self,
            "AutoscalerSecurityGroup",
            vpc=self.vpc,
            description="Allow ssh access to autoscaler instances",
            allow_all_outbound=True,
        )
        autoscaler_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(2376), "allow ssh access from the world"
        )
        instance_role = iam.Role(
            self,
            "AutoscalerInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                effect=iam.Effect.ALLOW,
                resources=["arn:aws:iam::*:role/cdk-*"],
            )
        )

        instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudformation:*", "s3:*"],
                effect=iam.Effect.ALLOW,
                resources=["*"],
            )
        )
        instance_profile = iam.CfnInstanceProfile(
            self,
            "autoscalerprofile",
            instance_profile_name="drone",
            roles=[instance_role.role_name],
        )

        autoscaler_task_def = task_def.add_container(
            "autoscaler",
            image=ecs.ContainerImage.from_registry("drone/autoscaler"),
            cpu=40,
            memory_reservation_mib=100,
            environment={
                "DRONE_SERVER_HOST": self.host_name,
                "DRONE_POOL_MIN": "0",
                "DRONE_AGENT_CONCURRENCY": "2",
                "DRONE_AMAZON_REGION": "us-west-2",
                "DRONE_AMAZON_SUBNET_ID": "subnet-9b2938c2",
                "DRONE_AMAZON_INSTANCE": "t3.medium",
                "DRONE_AMAZON_SECURITY_GROUP": autoscaler_sg.security_group_id,
                "DRONE_AMAZON_SSHKEY": "drone",
                "DRONE_AMAZON_IAM_PROFILE_ARN": instance_profile.attr_arn,
                "DRONE_AMAZON_VOLUME_TYPE": "gp3",
                "AWS_IAM": "true",
            },
            secrets={
                "DRONE_SERVER_TOKEN": self.get_ecs_secret("/drone/AUTOSCALER_TOKEN"),
                "DRONE_AGENT_TOKEN": self.drone_secret_shared,
            },
            port_mappings=[ecs.PortMapping(container_port=8080, host_port=8080)],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="autoscaler", log_retention=logs.RetentionDays.ONE_WEEK
            ),
        )
        task_def.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                effect=iam.Effect.ALLOW,
                resources=[instance_role.role_arn],
            )
        )
        task_def.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:DescribeInstances",
                    "ec2:DescribeKeyPairs",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeSubnets",
                    "ec2:CreateTags",
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                ],
                effect=iam.Effect.ALLOW,
                resources=["*"],
            )
        )
        task_def.add_volume(
            host=ecs.Host(source_path="/efs/drone"), name="drone-autoscaler"
        )
        autoscaler_task_def.add_mount_points(
            ecs.MountPoint(
                container_path="/data",
                read_only=False,
                source_volume="drone-autoscaler",
            )
        )
        service = ecs.CfnService(
            self,
            "autoscaler-service",
            cluster=self.cluster.cluster_name,
            deployment_configuration=ecs.CfnService.DeploymentConfigurationProperty(
                deployment_circuit_breaker=ecs.CfnService.DeploymentCircuitBreakerProperty(
                    enable=True, rollback=True
                ),
                maximum_percent=200,
                minimum_healthy_percent=100,
            ),
            deployment_controller=ecs.CfnService.DeploymentControllerProperty(
                type="ECS"
            ),
            desired_count=1,
            enable_execute_command=True,
            enable_ecs_managed_tags=True,
            launch_type="EC2",
            task_definition=task_def.task_definition_arn,
        )

    def get_ecs_secret(self, secret_path):
        return ecs.Secret.from_ssm_parameter(
            ssm.StringParameter.from_secure_string_parameter_attributes(
                self,
                secret_path.split("/")[-1],
                parameter_name=secret_path,
                version=1,
            )
        )

    def get_application(self):
        task_def = ecs.Ec2TaskDefinition(
            self,
            "TaskDef",
            volumes=[
                ecs.Volume(
                    name="docker-sock",
                    host=ecs.Host(source_path="/var/run/docker.sock"),
                )
            ],
        )
        server_img = DockerImageAsset(self, "ServerImage", directory="./server")
        agent_img = DockerImageAsset(self, "AgentImage", directory="./agent")

        server_task_def = task_def.add_container(
            "server",
            image=ecs.ContainerImage.from_docker_image_asset(server_img),
            cpu=20,
            memory_reservation_mib=128,
            environment={
                "DRONE_GITHUB_SERVER": "https://github.com",
                "DRONE_ADMIN": "ktruckenmiller",
                "DRONE_REPOSITORY_FILTER": "ktruckenmiller",
                "AWS_REGION": "us-west-2",
                "AWS_DEFAULT_REGION": "us-west-2",
                "DRONE_S3_BUCKET": self.s3_bucket.bucket_name,
                "DRONE_SERVER_HOST": self.host_name,
                "DRONE_SERVER_PROTO": "https",
                "DRONE_AGENTS_ENABLED": "true",
                "DRONE_LOGS_DEBUG": "true",
                "DRONE_JSONNET_ENABLED": "true",
                "DRONE_DATABASE_DRIVER": "mysql",
                "DRONE_GITHUB": "true",
            },
            secrets={
                "DRONE_RPC_SECRET": self.drone_secret_shared,
                "DRONE_GITHUB_CLIENT_ID": self.get_ecs_secret("/drone/GITHUB_CLIENT"),
                "DRONE_GITHUB_CLIENT_SECRET": self.get_ecs_secret(
                    "/drone/GITHUB_SECRET"
                ),
                "RDS_PASSWORD": self.get_ecs_secret("/drone/RDS_PASSWORD"),
                "RDS_HOST": self.get_ecs_secret("/drone/RDS_HOST"),
            },
            port_mappings=[ecs.PortMapping(container_port=80)],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="server", log_retention=logs.RetentionDays.ONE_WEEK
            ),
        )
        self.s3_bucket.grant_read_write(task_def.task_role)

        agent_task_def = task_def.add_container(
            "agent",
            image=ecs.ContainerImage.from_docker_image_asset(agent_img),
            cpu=40,
            memory_reservation_mib=256,
            environment={
                "DRONE_RPC_HOST": "drone-server",
                "DRONE_CPU_QUOTA": "90",
                "DRONE_RPC_DUMP_HTTP": "true",
                "DRONE_RPC_DUMP_HTTP_BODY": "true",
                "DRONE_RUNNER_CAPACITY": "2",
                "DRONE_RPC_PROTO": "http",
                "DRONE_DEBUG": "true",
                "AWS_REGION": "us-west-2",
                "AWS_DEFAULT_REGION": "us-west-2",
                "DRONE_LOGS_DEBUG": "true",
                "DRONE_RUNNER_NAME": "kloudcover-ec2",
            },
            secrets={"DRONE_RPC_SECRET": self.drone_secret_shared},
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="server", log_retention=logs.RetentionDays.ONE_WEEK
            ),
        )
        agent_task_def.add_mount_points(
            ecs.MountPoint(
                container_path="/var/run/docker.sock",
                read_only=False,
                source_volume="docker-sock",
            )
        )
        agent_task_def.add_link(container=server_task_def, alias="drone-server")

        tg1 = alb.ApplicationTargetGroup(
            self,
            "TG1",
            target_type=alb.TargetType.INSTANCE,
            vpc=self.vpc,
            health_check=alb.HealthCheck(
                enabled=True,
                healthy_http_codes="200-299",
                unhealthy_threshold_count=5,
                healthy_threshold_count=2,
                path="/healthz",
            ),
            protocol=alb.Protocol.HTTP,
            protocol_version=alb.ApplicationProtocolVersion.HTTP1,
            deregistration_delay=Duration.seconds(5),
        )
        listener = alb.ApplicationListener.from_lookup(
            self,
            "listener",
            listener_arn="arn:aws:elasticloadbalancing:us-west-2:601394826940:listener/app/kloudco-ALB-1XOWGRS4DIG1S/0d27cd3e97e641d1/fd04397ed274c342",
            load_balancer_arn=self.load_balancer.load_balancer_arn,
        )
        tg1.register_listener(listener)
        listener.add_certificates(
            "cert1",
            certificates=[
                certy.Certificate(
                    self,
                    "cert",
                    domain_name=self.host_name,
                    validation=certy.CertificateValidation.from_dns(self.hosted_zone),
                )
            ],
        )
        listener_rule = alb.ApplicationListenerRule(
            self,
            "ApplicationListenerRule",
            listener=listener,
            priority=22,
            conditions=[
                alb.ListenerCondition.host_headers([self.host_name]),
            ],
            target_groups=[tg1],
        )
        service = ecs.CfnService(
            self,
            "service",
            cluster=self.cluster.cluster_name,
            deployment_configuration=ecs.CfnService.DeploymentConfigurationProperty(
                deployment_circuit_breaker=ecs.CfnService.DeploymentCircuitBreakerProperty(
                    enable=True, rollback=True
                ),
                maximum_percent=200,
                minimum_healthy_percent=100,
            ),
            deployment_controller=ecs.CfnService.DeploymentControllerProperty(
                type="ECS"
            ),
            desired_count=1,
            enable_execute_command=True,
            enable_ecs_managed_tags=True,
            health_check_grace_period_seconds=10,
            launch_type="EC2",
            load_balancers=[
                ecs.CfnService.LoadBalancerProperty(
                    container_port=80,
                    # the properties below are optional
                    container_name=server_task_def.container_name,
                    target_group_arn=tg1.target_group_arn,
                )
            ],
            role=Fn.import_value("kloudcover-alb:ServiceRole"),
            task_definition=task_def.task_definition_arn,
        )
