import base64
import csv
import logging
import os
import time

import boto3
from ImageClassificationWebApp import settings

SQS = boto3.client('sqs', region_name='us-east-1')
S3 = boto3.client('s3')

_LOG = logging.getLogger(__name__)


def read_lookup_table(csv_file_path):
    try:
        lookup_table = {}
        with open(csv_file_path, mode='r') as infile:
            reader = csv.DictReader(infile)  # Assuming the CSV has headers
            for row in reader:
                # Assuming the CSV columns are named 'Image' and 'Results'
                lookup_table[row['Image']] = row['Results']
        return lookup_table
    except Exception as e:
        _LOG.error(f"Failed to read lookup table: {e}")
        return {}


# Load the lookup table at the start, so it's only read once
dir_path = os.path.dirname(os.path.realpath(__file__))
lookup_table_path = os.path.join(dir_path, 'dataset/Classification Results on Face Dataset (1000 images).csv')
lookup_table = read_lookup_table(lookup_table_path)


def handle():
    while True:
        response = SQS.receive_message(
            QueueUrl=settings.REQ_QUEUE_URL,
            AttributeNames=['All'],
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0
        )
        if 'Messages' not in response:
            time.sleep(5)
            continue

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        attrs = {k: v['StringValue'] for k, v in message['MessageAttributes'].items()}
        print(f'Received message has attrs: {attrs}')

        image = base64.b64decode(message['Body'])  # binary data
        S3.put_object(
            Body=image,
            Bucket=settings.S3_IN_BUCKET,
            Key=f"{attrs['request_id']}_{attrs['filename']}",
        )

        fname = attrs['filename'].split('.')[0]
        classification_result = lookup_table.get(fname, 'Not Found')
        result = f"{fname}:{classification_result}"

        SQS.send_message(
            QueueUrl=settings.RESP_QUEUE_URL,
            MessageBody=result,
            MessageAttributes={
                'request_id': {
                    'StringValue': attrs['request_id'],
                    'DataType': 'String'
                },
            },
        )
        S3.put_object(
            Body=result,
            Bucket=settings.S3_OUT_BUCKET,
            Key=f"{attrs['request_id']}_{fname}.txt"
        )
        # Delete received message from queue
        SQS.delete_message(
            QueueUrl=settings.REQ_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )

        if os.path.isfile(os.path.join(settings.TRAFFIC_DIRECTORY, attrs['request_id'])):
            os.remove(os.path.join(settings.TRAFFIC_DIRECTORY, attrs['request_id']))


if __name__ == '__main__':
    handle()
