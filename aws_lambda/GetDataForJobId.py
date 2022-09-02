import json
import boto3
import os

s3_client = boto3.client('s3', aws_access_key_id=os.environ['ACCESS_KEY'],
                         aws_secret_access_key=os.environ['SECRET_KEY'])


def lambda_handler(event, context):
    try:
        if event['params']['header']['Authorization'] != os.environ['TOKEN']:
            return {'message': 'Access Token mismatch', 'statusCode': 403}
    except KeyError:
        return {'message': 'Access Token Error', 'statusCode': 403}
    try:
        s3_client_obj = s3_client.get_object(Bucket=os.environ['BUCKET_NAME'],
                                             Key=f"processed/{event['params']['querystring']['job_id']}.json")
        result = json.loads(s3_client_obj['Body'].read().decode('utf-8')).get('transcription_results')
        return {'data': result, 'message': 'Success', 'status': 200}
    except Exception as e:
        return {'message': str(e), 'status': 404}
