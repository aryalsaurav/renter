{
    "taskDefinitionArn": "arn:aws:ecs:ap-south-1:264595824735:task-definition/renter-web:18",
    "containerDefinitions": [
        {
            "name": "server",
            "image": "264595824735.dkr.ecr.ap-south-1.amazonaws.com/renter:738ef28",
            "cpu": 0,
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "protocol": "tcp",
                    "name": "server-8000-tcp",
                    "appProtocol": "http"
                }
            ],
            "essential": true,
            "command": [
                "gunicorn",
                "config.wsgi:application",
                "--bind",
                "0.0.0.0:8000"
            ],
            "environment": [],
            "environmentFiles": [
                {
                    "value": "arn:aws:s3:::renter-bucket-env/renter.env",
                    "type": "s3"
                }
            ],
            "mountPoints": [],
            "volumesFrom": [],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/renter-web",
                    "awslogs-create-group": "true",
                    "awslogs-region": "ap-south-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "systemControls": []
        }
    ],
    "family": "renter-web",
    "taskRoleArn": "arn:aws:iam::264595824735:role/S3Role",
    "executionRoleArn": "arn:aws:iam::264595824735:role/ecsTaskExecutionRole",
    "networkMode": "awsvpc",
    "revision": 18,
    "volumes": [],
    "status": "ACTIVE",
    "requiresAttributes": [
        {
            "name": "com.amazonaws.ecs.capability.logging-driver.awslogs"
        },
        {
            "name": "ecs.capability.execution-role-awslogs"
        },
        {
            "name": "com.amazonaws.ecs.capability.ecr-auth"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"
        },
        {
            "name": "ecs.capability.env-files.s3"
        },
        {
            "name": "com.amazonaws.ecs.capability.task-iam-role"
        },
        {
            "name": "ecs.capability.execution-role-ecr-pull"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
        },
        {
            "name": "ecs.capability.task-eni"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.29"
        }
    ],
    "placementConstraints": [],
    "compatibilities": [
        "EC2",
        "MANAGED_INSTANCES"
    ],
    "runtimePlatform": {
        "cpuArchitecture": "X86_64",
        "operatingSystemFamily": "LINUX"
    },
    "requiresCompatibilities": [
        "EC2"
    ],
    "cpu": "512",
    "memory": "717",
    "registeredAt": "2026-06-21T10:03:07.061Z",
    "registeredBy": "arn:aws:sts::264595824735:assumed-role/RenterProdDeployRole/GitHubActions",
    "enableFaultInjection": false,
    "tags": []
}