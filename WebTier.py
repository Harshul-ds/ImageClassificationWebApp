from flask import Flask, request
import boto3
import time
import json
import os

app = Flask(__name__)

# Assuming AWS credentials are set in environment variables or IAM role
sqs = boto3.client('sqs', region_name='us-east-1')

req_queue_url = 'https://sqs.us-east-1.amazonaws.com/339713028482/1229378256-req-queue'
resp_queue_url = 'https://sqs.us-east-1.amazonaws.com/339713028482/1229378256-resp-queue'

@app.route('/', methods=['GET'])
def handle_req():
    return "Service is up"

@app.route('/', methods=['POST'])
def handle_image():
    image_file = request.files['inputFile']
    filename = image_file.filename
    
    # Save the file temporarily
    temp_file_path = os.path.join('/tmp', filename)
    image_file.save(temp_file_path)
    
    # Generate a unique ID for this request, could use filename or a combination of filename and timestamp
    request_id = filename.split('.')[0]  # Assuming the filename is 'test_00.jpg', strip extension for ID

    # Send the request to the request queue with filename and request_id
    sqs.send_message(
        QueueUrl=req_queue_url,
        MessageBody=json.dumps({'filename': filename, 'request_id': request_id})
    )

    # Poll the response queue for the corresponding response
    while True:
        resp = sqs.receive_message(
            QueueUrl=resp_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10  # Use long polling
        )

        # Check if a message was received
        if 'Messages' in resp:
            message = resp['Messages'][0]
            body = json.loads(message['Body'])

            # Check if the response is for the current request
            if body['request_id'] == request_id:
                # Delete the message from the queue to prevent reprocessing
                sqs.delete_message(
                    QueueUrl=resp_queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                # Return the classification result
                return f"{body['filename']}:{body['classification_result']}"

            # Not the right message, return it to the queue
            else:
                sqs.change_message_visibility(
                    QueueUrl=resp_queue_url,
                    ReceiptHandle=message['ReceiptHandle'],
                    VisibilityTimeout=0  # Make the message immediately visible again
                )

        # No message for this request yet, continue polling
        else:
            time.sleep(5)  # Sleep for a short period to avoid hitting rate limits

    # If the loop exits without returning, something went wrong
    return "Error processing request", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)  # Make sure to listen on port 8000 as per requirements
