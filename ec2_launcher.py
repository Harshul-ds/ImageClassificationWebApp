import os

import boto3
from ImageClassificationWebApp import settings

EC2 = boto3.client('ec2', region_name='us-east-1')
REQ_TO_INSTANCE_RATIO = 50  # 1 instance per 50 requests


def launch_instance(name='app-tier-instance-0', itype='t2.micro'):
    return EC2.run_instances(
        InstanceType=itype,
        MinCount=1,
        MaxCount=1,
        KeyName='EC2key',
        ImageId="ami-0dec28adf912e7a8a",
        SecurityGroupIds=['sg-0e5641dcf17dcae9a'],
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
        instances = os.listdir(settings.INSTANCE_DIRECTORY)
        if not files and not instances:
            return

        open(os.path.join(settings.INSTANCE_DIRECTORY, None), 'a').close()

        needed_instances = (len(files) // REQ_TO_INSTANCE_RATIO) + 1
        if needed_instances > len(instances):
            for i in range(len(instances), needed_instances):
                instance = launch_instance(name=f'app-tier-instance-{i}')
                open(os.path.join(settings.INSTANCE_DIRECTORY, instance['Instances'][0]['InstanceId']), 'a').close()

        elif needed_instances < len(instances):
            for i in range(len(instances) - 1, needed_instances - 1, -1):
                instance = instances.pop()
                instance_id = instance['Instances'][0]['InstanceId']

                EC2.terminate_instances(
                    InstanceIds=[instance_id],
                )
                if os.path.isfile(os.path.join(settings.INSTANCE_DIRECTORY, instance_id)):
                    os.remove(os.path.join(settings.INSTANCE_DIRECTORY, instance_id))


if __name__ == '__main__':
    autoscaler()
