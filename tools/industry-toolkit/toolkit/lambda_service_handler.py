import boto3
import os
import json
import time

dynamodb = boto3.resource('dynamodb')
ecs_client = boto3.client('ecs')

TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME')
ECS_CLUSTER_NAME = os.getenv('ECS_CLUSTER_NAME')
TASK_DEFINITION_ARN = os.getenv('TASK_DEFINITION_ARN')
SUBNET_ID = os.getenv('SUBNET_ID')

def lambda_handler(event, context):
    http_method = event['httpMethod']

    if http_method == 'GET':
        return handle_get(event)
    elif http_method == 'POST':
        return handle_post(event)
    else:
        return {
            'statusCode': 405,
            'body': json.dumps('Method Not Allowed')
        }

def handle_get(event):
    service_id = event['queryStringParameters'].get('id')
    if not service_id:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing id parameter')
        }

    table = dynamodb.Table(TABLE_NAME)
    response = table.get_item(Key={'id': service_id})

    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps('Record not found')
        }

    return {
        'statusCode': 200,
        'body': json.dumps(response['Item'])
    }

def handle_post(event):
    body = event.get('body')
    if not body:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing request body')
        }

    response = ecs_client.run_task(
        cluster=ECS_CLUSTER_NAME,
        launchType="FARGATE",
        taskDefinition=TASK_DEFINITION_ARN,
        overrides={
            'containerOverrides': [
                {
                    'name': 'IndustryToolkitContainer',
                    'environment': [
                        {'name': 'SERVICE_BODY', 'value': body}
                    ]
                }
            ]
        },
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [SUBNET_ID],
                'assignPublicIp': 'ENABLED'
            }
        }
    )

    task_arn = response['tasks'][0]['taskArn']

    while True:
        task_status = ecs_client.describe_tasks(cluster=ECS_CLUSTER_NAME, tasks=[task_arn])
        task_state = task_status['tasks'][0]['lastStatus']

        if task_state == 'STOPPED':
            exit_code = task_status['tasks'][0]['containers'][0].get('exitCode', -1)
            if exit_code == 0:
                return {
                    'statusCode': 200,
                    'body': json.dumps('ECS task completed successfully')
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'ECS task failed with exit code {exit_code}')
                }

        time.sleep(5)  # Poll every 5 seconds
