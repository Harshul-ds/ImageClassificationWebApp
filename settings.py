import configparser
import os

c = configparser.ConfigParser()
DEFAULT_PROFILE = 'default'
AWS_CREDS_PATH = os.path.join(os.path.expanduser("~"), '.aws/credentials')
c.read(AWS_CREDS_PATH)

REQ_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/339713028482/1229378256-req-queue'
RESP_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/339713028482/1229378256-resp-queue'
S3_IN_BUCKET = '1229378256-in-bucket'
S3_OUT_BUCKET = '1229378256-out-bucket'
TRAFFIC_DIRECTORY = '/tmp/traffic'
INSTANCE_DIRECTORY = '/tmp/instances'

AWS_ACCESS_KEY_ID = c.get(DEFAULT_PROFILE, 'aws_access_key_id')
AWS_SECRET_ACCESS_KEY = c.get(DEFAULT_PROFILE, 'aws_secret_access_key')
