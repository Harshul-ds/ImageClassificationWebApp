import os
import time

import boto3

import settings

EC2 = boto3.client('ec2', region_name='us-east-1')
REQ_TO_INSTANCE_RATIO = 10
MAX_INSTANCES = 20
SCALING_POLL_INTERVAL = 60  # seconds


def launch_command():
    return """#!/bin/bash
    export PYTHONPATH=/home/ubuntu/;
    python3 /home/ubuntu/ImageClassificationWebApp/AppTier/AppTier.py;"""


def launch_instance(name='app-tier-instance-0', itype='t2.micro'):
    return EC2.run_instances(
        InstanceType=itype,
        MinCount=1,
        MaxCount=1,
        KeyName='EC2key',
        ImageId=os.getenv('AMI_INSTANCE', 'ami-xxxx'),
        SecurityGroupIds=['sg-0e5641dcf17dcae9a'],
        UserData=launch_command(),
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': name
                    },
                ]
            },
        ],
    )


def autoscaler():
    if not os.path.exists(settings.INSTANCE_DIRECTORY):
        os.mkdir(settings.INSTANCE_DIRECTORY)

    while True:
        time.sleep(SCALING_POLL_INTERVAL)

        files = os.listdir(settings.TRAFFIC_DIRECTORY)
        instances = os.listdir(settings.INSTANCE_DIRECTORY)
        if not files and not instances:
            continue

        if not files:
            needed_instances = 0
        else:
            needed_instances = max(1, len(files) // REQ_TO_INSTANCE_RATIO)

        if needed_instances > len(instances) and len(instances) < MAX_INSTANCES:
            for i in range(len(instances), needed_instances):
                instance = launch_instance(name=f'app-tier-instance-{i}')
                open(os.path.join(settings.INSTANCE_DIRECTORY, instance['Instances'][0]['InstanceId']), 'a').close()
                print(f'Creating Instance:\n{instance}')

        elif needed_instances < len(instances):
            for i in range(len(instances), needed_instances, -1):
                instance_id = instances.pop()

                EC2.terminate_instances(
                    InstanceIds=[instance_id],
                )
                print(f'Terminating Instance:\n{instance_id}')
                if os.path.isfile(os.path.join(settings.INSTANCE_DIRECTORY, instance_id)):
                    os.remove(os.path.join(settings.INSTANCE_DIRECTORY, instance_id))


if __name__ == '__main__':
    autoscaler()
