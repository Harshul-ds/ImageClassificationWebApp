import base64

import boto3
from ImageClassificationWebApp import settings

SQS = boto3.client('sqs', region_name='us-east-1')
S3 = boto3.client('s3')


def handle():
    while True:
        response = SQS.receive_message(
            QueueUrl=settings.REQ_QUEUE_URL,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0
        )
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        attrs = message['MessageAttributes']
        print(f'Received message has attrs: {attrs}')

        image = base64.b64decode(message['Body'])  # binary data
        S3.put_object(
            Body=image,
            Bucket=settings.S3_IN_BUCKET,
            Key=f"{attrs['request_id']}_{attrs['filename']}.jpg",
        )
        # TODO: Handle model inference logic. Lookup or whatever
        data = {}  # get the result
        result = f"{data['filename']}:{data['classification_result']}"

        # if result not correct: delete message or keep? how to handle? or simply ignore?

        SQS.send_message(
            QueueUrl=settings.RESP_QUEUE_URL,
            MessageBody=result,
            MessageAttributes={
                'request_id': {
                    'StringValue': attrs['request_id'],
                    'DataType': 'string'
                },
            },
        )
        S3.put_object(
            Body=result,
            Bucket=settings.S3_OUT_BUCKET,
            Key=f"{attrs['request_id']}_{attrs['filename']}.txt"
        )
        # Delete received message from queue
        SQS.delete_message(
            QueueUrl=settings.REQ_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )


if __name__ == '__main__':
    handle()
