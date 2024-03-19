REQ_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/339713028482/1229378256-req-queue'
RESP_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/339713028482/1229378256-resp-queue'
S3_IN_BUCKET = '1229378256-in-bucket'
S3_OUT_BUCKET = '1229378256-out-bucket'
# Use the AMI ID from the image you provided
APP_AMI_ID = 'ami-080e1f13689e07408'

# The instance type from the image is t2.micro
APP_INSTANCE_TYPE = 't2.micro'

# Assumed value based on your application's performance
MESSAGES_PER_INSTANCE = 10

# As per your document, you can have a maximum of 20 App Tier instances
MAX_APP_INSTANCES = 20

# Interval for the autoscaler to check the queue (in seconds)
SCALING_POLL_INTERVAL = 60