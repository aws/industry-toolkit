import json
from flask import Flask, jsonify, request
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.metrics import Metrics, MetricUnit

# Initialize Logger, Tracer, and Metrics
logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="MyApp", service="MyService")

# Initialize Flask app
app = Flask(__name__)

@app.route("/services", methods=["GET"])
@tracer.capture_method
def get_service():
    """Handles GET requests for /services"""
    logger.info("Received GET request for /services")
    
    # Add metrics for monitoring GET requests
    metrics.add_metric(name="GetServiceRequests", unit=MetricUnit.Count, value=1)
    
    # Example response
    response = {
        "message": "This is a GET response from /services",
        "data": {"serviceId": 123, "serviceName": "ExampleService"}
    }
    return jsonify(response), 200

@app.route("/services", methods=["POST"])
@tracer.capture_method
def post_service():
    """Handles POST requests for /services"""
    logger.info("Received POST request for /services")
    
    # Parse the JSON payload
    data = request.json
    service_name = data.get("serviceName", "Unknown Service")

    logger.debug(f"Paylod: {data}")
    
    # Log metrics for POST requests
    metrics.add_metric(name="PostServiceRequests", unit=MetricUnit.Count, value=1)
    
    # Example response
    response = {
        "message": f"Received service: {service_name}",
        "data": data
    }
    return jsonify(response), 201

