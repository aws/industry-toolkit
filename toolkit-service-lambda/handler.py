import json
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.metrics import Metrics, MetricUnit
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent, APIGatewayProxyResponse
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize Logger, Tracer, and Metrics
logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="MyApp", service="MyService")

@logger.inject_lambda_context
@metrics.log_metrics
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Lambda function to handle API Gateway events for /services"""
    api_event = APIGatewayProxyEvent(event)  # Parse event into APIGatewayProxyEvent for easier access

    # Check for the path and HTTP method to route to the correct logic
    if api_event.resource == "/services" and api_event.http_method == "POST":
        return handle_post_service(api_event)
    elif api_event.resource.startswith("/services/") and api_event.http_method == "GET":
        service_id = api_event.path_parameters.get("id")  # Get {id} from path parameters
        return handle_get_service(service_id)
    else:
        # Return a 404 Not Found if no routes match
        return APIGatewayProxyResponse(
            status_code=404,
            body=json.dumps({"message": "Not Found"})
        ).to_dict()


def handle_get_service(service_id: str) -> dict:
    """Handles GET requests for /services/{id}"""
    logger.info(f"Received GET request for /services/{service_id}")

    metrics.add_metric(name="GetServiceRequests", unit=MetricUnit.Count, value=1)

    # Example response
    response = {
        "message": f"This is a GET response for service with ID: {service_id}",
        "data": {"serviceId": service_id, "serviceName": "ExampleService"}
    }
    return APIGatewayProxyResponse(
        status_code=200,
        body=json.dumps(response)
    ).to_dict()


def handle_post_service(api_event: APIGatewayProxyEvent) -> dict:
    """Handles POST requests for /services"""
    logger.info("Received POST request for /services")

    # Parse the JSON payload
    data = api_event.json_body
    service_name = data.get("serviceName", "Unknown Service")

    logger.debug(f"Event: {data}")

    # Log metrics for POST requests
    metrics.add_metric(name="PostServiceRequests", unit=MetricUnit.Count, value=1)

    # Example response
    response = {
        "message": f"Received service: {service_name}",
        "data": data
    }
    return APIGatewayProxyResponse(
        status_code=201,
        body=json.dumps(response)
    ).to_dict()
