import os

import boto3
from ImageClassificationWebApp import settings

EC2 = boto3.client('ec2', region_name='us-east-1')
instances = []
REQ_TO_INSTANCE_RATIO = 50  # 1 instance per 50 requests


def launch_instance(name='app-tier-instance-0', itype='t2.micro'):
    return EC2.run_instances(
        InstanceType=itype,
        MinCount=1,
        MaxCount=1,
        KeyName='EC2key',
        ImageId="ami-0dec28adf912e7a8a",
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
    while True:
        files = os.listdir(settings.TRAFFIC_DIRECTORY)
        if not files and not instances:
            return

        needed_instances = (len(files) // REQ_TO_INSTANCE_RATIO) + 1
        if needed_instances > len(instances):
            for i in range(len(instances), needed_instances):
                instances.append(launch_instance(name=f'app-tier-instance-{i}'))

        elif needed_instances < len(instances):
            for i in range(len(instances) - 1, needed_instances - 1, -1):
                instance = instances.pop()
                EC2.terminate_instances(
                    InstanceIds=[
                        instance['Instances'][0]['InstanceId'],
                    ],
                )


if __name__ == '__main__':
    autoscaler()
