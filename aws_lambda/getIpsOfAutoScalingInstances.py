import boto3
import json
import os

ACCESS_KEY = os.environ['ACCESS_KEY']
SECRET_KEY = os.environ['SECRET_KEY']

client = boto3.client(
    'autoscaling',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-1'
)
ec2 = boto3.resource(
    'ec2',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-1'
)


def lambda_handler(event, context):
    # TODO implement
    autoscaling_group_name = []
    autoscaling_group_name.append(event.get('autoscaling_group_name', None))

    if autoscaling_group_name[0] is None:
        return {'message': "autoscaling_group_name error!", 'statusCode': 400}
    print("######## AutoScalingGroup:::", autoscaling_group_name)
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=autoscaling_group_name,
        MaxRecords=100)

    try:
        instance_data = response.get('AutoScalingGroups')[0].get('Instances', [])
        instance_ids = []
        result = []

        for instance in instance_data:
            instance_ids.append(instance.get('InstanceId'))

        for id in instance_ids:
            result.append(f'http://{ec2.Instance(id).public_ip_address}:5555/tasks?state=STARTED')

        return {'data': result, 'message': "Success!", 'statusCode': 200}
    except Exception as e:
        return {'message': json.dumps(e)}
