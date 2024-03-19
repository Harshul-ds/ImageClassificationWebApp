import base64
import datetime
import boto3
import json
import logging
import uuid
from flask import Flask, request, jsonify
import settings  # Ensure this contains your configuration, including REQ_QUEUE_URL and RESP_QUEUE_URL

app = Flask(__name__)
SQS = boto3.client('sqs', region_name='us-east-1')

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

@app.route('/', methods=['GET'])
def handle_req():
    return "Service is up"

@app.route('/', methods=['POST'])
def handle_image():
    try:
        if 'inputFile' not in request.files:
            logger.error("No inputFile in request.files")
            return jsonify({'error': 'No File Provided'}), 400

        image_file = request.files['inputFile']
        request_id = str(uuid.uuid4())

        image_file.seek(0)
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        SQS.send_message(
            QueueUrl=settings.REQ_QUEUE_URL,
            MessageBody=json.dumps({'image_data': encoded_image}),
            MessageAttributes={
                'request_id': {'StringValue': request_id, 'DataType': 'String'},
                'timestamp': {'StringValue': datetime.datetime.now().isoformat(), 'DataType': 'String'},
                'filename': {'StringValue': image_file.filename, 'DataType': 'String'}
            },
        )
        logger.info(f"Sent image with RequestID: {request_id} to SQS.")

        # Poll the response queue for the result
        while True:
            response_messages = SQS.receive_message(
                QueueUrl=settings.RESP_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # Long polling
                MessageAttributeNames=['All']
            )
            if 'Messages' in response_messages:
                for message in response_messages['Messages']:
                    resp_attrs = message.get('MessageAttributes', {})
                    if 'request_id' in resp_attrs and resp_attrs['request_id']['StringValue'] == request_id:
                        classification_result = message['Body']
                        # Delete the message from the response queue
                        SQS.delete_message(
                            QueueUrl=settings.RESP_QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        return f"{image_file.filename}:{classification_result}", 200

        # Implement a timeout mechanism as needed
        # return jsonify({'error': 'Timeout waiting for classification result'}), 504
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
