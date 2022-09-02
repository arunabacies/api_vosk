import json
import boto3
import os
import urllib.parse

ACCESS_KEY = os.environ['ACCESS_KEY']
SECRET_KEY = os.environ['SECRET_KEY']
APP_NAME = os.environ['APP_NAME']

aws_lambda = boto3.client(
    'lambda',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-1'
)

s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-1'
)


def lambda_handler(event, context):
    # TODO implement
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + response['ContentType'])
        env_variables = json.loads(response['Body'].read().decode('utf-8'))

        lambda_config = aws_lambda.get_function_configuration(
            FunctionName=APP_NAME,
        )
        existing_env_variables = lambda_config['Environment']['Variables']
        for key in env_variables:
            existing_env_variables[key] = str(env_variables[key])

        print(existing_env_variables)
        lambda_response = aws_lambda.update_function_configuration(
            FunctionName=APP_NAME,
            Environment={
                'Variables': existing_env_variables
            })
        return response['ContentType']
    except Exception as e:
        print(e)
        print(
            'Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(
                key, bucket))
        raise e
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
