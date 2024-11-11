import json
import boto3
from flask import Flask, request
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.data_classes.api_gateway_proxy_event import Response

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table("ServicesTable")

@app.route('/services', methods=['GET'])
def get_service():
    service_id = request.args.get('id')
    if not service_id:
        return {"error": "Missing id parameter"}, 400
    response = table.get_item(Key={'id': service_id})
    if 'Item' not in response:
        return {"error": "Record not found"}, 404
    return response['Item'], 200

@app.route('/services', methods=['POST'])
def create_service():
    data = request.get_json()
    if not data:
        return {"error": "Missing request body"}, 400

    print(data)
    return {"message": "Service created successfully"}, 201

def lambda_handler(event, context):
    print(here)
    event = APIGatewayProxyEvent(event)
    print(event)
    return Response(app.wsgi_app(event), context)
