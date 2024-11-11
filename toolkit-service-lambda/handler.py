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

@app.route("/services/<id>", methods=["GET"])
@tracer.capture_method
def get_service(id):
    """Handles GET requests for /services/{id}"""
    logger.info(f"Received GET request for /services/{id}")

    metrics.add_metric(name="GetServiceRequests", unit=MetricUnit.Count, value=1)

    response = {
        "message": f"This is a GET response for service with ID: {id}",
        "data": {"serviceId": id, "serviceName": "ExampleService"}
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

    # Log metrics for POST requests
    metrics.add_metric(name="PostServiceRequests", unit=MetricUnit.Count, value=1)

    # Example response
    response = {
        "message": f"Received service: {service_name}",
        "data": data
    }
    return jsonify(response), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
