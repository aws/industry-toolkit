from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext

app = APIGatewayRestResolver()

@app.post("/services")
def post_services():
    return {"message": "pong"}

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
