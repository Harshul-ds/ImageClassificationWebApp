import boto3
import time
import logging
import settings  # Make sure this module contains all necessary configurations

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

EC2 = boto3.resource('ec2', region_name='us-east-1')
SQS = boto3.client('sqs', region_name='us-east-1')

def check_queue_length():
    """Check the number of messages in the request queue."""
    response = SQS.get_queue_attributes(
        QueueUrl=settings.REQ_QUEUE_URL,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    return int(response['Attributes']['ApproximateNumberOfMessages'])

def adjust_instances(target_count):
    """Adjust the number of App Tier instances to the target count."""
    current_instances = list(EC2.instances.filter(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['app-tier-instance']},
            {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
        ]
    ))
    current_count = len(current_instances)

    if current_count < target_count:
        # Launch new instances
        to_launch = target_count - current_count
        logger.info(f"Launching {to_launch} new App Tier instances.")
        EC2.create_instances(
            ImageId=settings.APP_AMI_ID,
            MinCount=to_launch,
            MaxCount=to_launch,
            InstanceType=settings.APP_INSTANCE_TYPE,
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'app-tier-instance'}]}]
        )
    elif current_count > target_count:
        # Terminate excess instances
        to_terminate = current_instances[:current_count - target_count]
        logger.info(f"Terminating {len(to_terminate)} excess App Tier instances.")
        for instance in to_terminate:
            instance.terminate()

def autoscale():
    """Check the queue length and adjust the number of instances accordingly."""
    queue_length = check_queue_length()
    target_count = min(max(queue_length // settings.MESSAGES_PER_INSTANCE, 1), settings.MAX_APP_INSTANCES)  # Ensure at least 1 instance
    adjust_instances(target_count)

if __name__ == '__main__':
    while True:
        autoscale()
        time.sleep(settings.SCALING_POLL_INTERVAL)  # Wait before the next check
