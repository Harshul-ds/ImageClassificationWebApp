import base64
import datetime

import boto3
import time
import json
import os
import uuid

from flask import Flask, request
from ImageClassificationWebApp import settings

app = Flask(__name__)

# Assuming AWS credentials are set in environment variables or IAM role
SQS = boto3.client('sqs', region_name='us-east-1')


@app.route('/', methods=['GET'])
def handle_req():
    return "Service is up"


@app.route('/', methods=['POST'])
def handle_image():
    if 'inputFile' not in request.files:
        return 'No File Provided', 400

    if not os.path.exists(settings.TRAFFIC_DIRECTORY):
        os.mkdir(settings.TRAFFIC_DIRECTORY)

    image_file = request.files['inputFile']

    # Save the file temporarily
    # temp_file_path = os.path.join('/tmp', filename)
    # image_file.save(temp_file_path)
    
    # Generate a unique ID for this request, could use filename or a combination of filename and timestamp
    request_id = str(uuid.uuid4())

    open(os.path.join(settings.TRAFFIC_DIRECTORY, request_id), 'a').close()

    # Send the request to the request queue with filename and request_id
    response = SQS.send_message(
        QueueUrl=settings.REQ_QUEUE_URL,
        MessageBody=base64.b64encode(image_file.read()).decode('utf-8'),
        MessageAttributes={
            'request_id': {
                'StringValue': request_id,
                'DataType': 'string'
            },
            'timestamp': {
                'StringValue': datetime.datetime.now().strftime('"%Y-%m-%d %H:%M:%S"'),
                'DataType': 'string'
            },
            'filename': {
                'StringValue': image_file.filename,
                'DataType': 'string'
            }
        },
    )
    print(f'Sent image with RequestID: {response["MessageId"]}')

    # Poll the response queue for the corresponding response
    print('Waiting for response...')
    while True:
        resp = SQS.receive_message(
            QueueUrl=settings.RESP_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0,
            AttributeNames=['All']
        )
        # Check if a message was received
        if 'Messages' in resp:
            message = resp['Messages'][0]
            attrs = message['MessageAttributes']
            body = message['Body']

            # Check if the response is for the current request
            if not attrs['request_id'] == request_id:
                # Not the right message, return it to the queue
                SQS.change_message_visibility(
                    QueueUrl=settings.RESP_QUEUE_URL,
                    ReceiptHandle=message['ReceiptHandle'],
                    VisibilityTimeout=0  # Make the message immediately visible again
                )
                continue

            print(f'Message received with body: {body}')
            # Delete the message from the queue to prevent reprocessing
            SQS.delete_message(
                QueueUrl=settings.RESP_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
            # Return the classification result
            return body

        # No message for this request yet, continue polling
        else:
            time.sleep(5)  # Sleep for a short period to avoid hitting rate limits

    # If the loop exits without returning, something went wrong
    return "Error processing request", 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)  # Make sure to listen on port 8000 as per requirements
