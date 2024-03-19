import base64
import boto3
import csv
import json
import logging
import settings  # Ensure this contains configuration for AWS resources and CSV file path

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

SQS = boto3.client('sqs', region_name='us-east-1')
S3 = boto3.client('s3')

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
        logger.error(f"Failed to read lookup table: {e}")
        return {}

# Load the lookup table at the start, so it's only read once
lookup_table = read_lookup_table('./dataset/Classification Results on Face Dataset (1000 images).csv')

def handle_message():
    response = SQS.receive_message(
        QueueUrl=settings.REQ_QUEUE_URL,
        AttributeNames=['All'],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20,
        MessageAttributeNames=['All']
    )

    if 'Messages' in response:
        for message in response['Messages']:
            try:
                receipt_handle = message['ReceiptHandle']
                attrs = message.get('MessageAttributes', {})

                # Decode the image data (assuming it's base64 encoded in the message body)
                image_data = base64.b64decode(json.loads(message['Body'])['image_data'])

                # Save the image to the S3 input bucket
                request_id = attrs.get('request_id', {}).get('StringValue', 'Unknown')
                filename = attrs.get('filename', {}).get('StringValue', 'Unknown')
                S3.put_object(
                    Body=image_data,
                    Bucket=settings.S3_IN_BUCKET,
                    Key=f"{request_id}_{filename}",
                )

                # Extract the classification result using the filename from the lookup table
                # Assuming filename without extension is used as the key in the lookup table
                image_key = filename.replace('.jpg', '')  # Removing the file extension if present
                classification_result = lookup_table.get(image_key, "Not Found")

                # Save the result to the S3 output bucket
                S3.put_object(
                    Body=classification_result,
                    Bucket=settings.S3_OUT_BUCKET,
                    Key=f"{request_id}_{filename}.txt"
                )

                # Send classification result back via SQS
                SQS.send_message(
                    QueueUrl=settings.RESP_QUEUE_URL,
                    MessageBody=f"{classification_result}",
                    MessageAttributes={
                        'request_id': {'StringValue': request_id, 'DataType': 'String'},
                    },
                )

                # Delete the message from the request queue
                SQS.delete_message(
                    QueueUrl=settings.REQ_QUEUE_URL,
                    ReceiptHandle=receipt_handle
                )
            except KeyError as e:
                logger.error(f"KeyError handling message: {e}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")

if __name__ == '__main__':
    while True:
        handle_message()
