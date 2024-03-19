import os
import boto3

import settings

EC2 = boto3.client('ec2', region_name='us-east-1')
REQ_TO_INSTANCE_RATIO = 50  # 1 instance per 50 requests


def launch_command():
    return """#!/bin/bash python3 ImageClassificationWebApp/AppTier/AppTier.py"""


def launch_instance(name='app-tier-instance-0', itype='t2.micro'):
    return EC2.run_instances(
        InstanceType=itype,
        MinCount=1,
        MaxCount=1,
        KeyName='EC2key',
        ImageId="ami-0679b66fdb562f324",
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
        files = os.listdir(settings.TRAFFIC_DIRECTORY)
        instances = os.listdir(settings.INSTANCE_DIRECTORY)
        if not files and not instances:
            continue

        if not files:
            needed_instances = 0
        else:
            needed_instances = (len(files) // REQ_TO_INSTANCE_RATIO) + 1

        if needed_instances > len(instances):
            for i in range(len(instances), needed_instances):
                instance = launch_instance(name=f'app-tier-instance-{i}')
                open(os.path.join(settings.INSTANCE_DIRECTORY, instance['Instances'][0]['InstanceId']), 'a').close()
                print(f'Creating Instance:\n{instance}')

        elif needed_instances < len(instances):
            for i in range(len(instances) - 1, needed_instances - 1, -1):
                instance_id = instances.pop()

                EC2.terminate_instances(
                    InstanceIds=[instance_id],
                )
                print(f'Terminating Instance:\n{instance_id}')
                if os.path.isfile(os.path.join(settings.INSTANCE_DIRECTORY, instance_id)):
                    os.remove(os.path.join(settings.INSTANCE_DIRECTORY, instance_id))


if __name__ == '__main__':
    autoscaler()
