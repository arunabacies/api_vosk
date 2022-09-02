import json
import boto3
import os
import hashlib

ACCESS_KEY = os.environ['ACCESS_KEY']
SECRET_KEY = os.environ['SECRET_KEY']
QUEUE_NAME = os.environ['QUEUE_NAME']
TOKEN = os.environ['TOKEN']
sqs = boto3.resource(
    'sqs',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)


def lambda_handler(event, context):
    print(event)
    data = event.get('body', {})
    print(event['params'])
    try:
        token = event['params']['header']['Authorization']
        if token == TOKEN:
            queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)
            hash_object = hashlib.sha256(json.dumps(data).encode('utf-8'))
            hex_dig = hash_object.hexdigest()
            response = queue.send_message(MessageBody=json.dumps({'job_id': hex_dig, **data}))
            print({'job_id': hex_dig, **data})
            return {'job_id': hex_dig}
        else:
            return {'message': 'Access Token mismatch', 'statusCode': 403}

    except KeyError:
        return {'message': 'Access Token Error', 'statusCode': 403}
