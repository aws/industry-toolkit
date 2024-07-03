import boto3
import json
import argparse

def resolve_model_id(model_name):
    model_ids = {
        "haiku": "anthropic.claude-3-haiku-20240307-v1:0",
        "sonnet": "anthropic.claude-3-sonnet-20240229-v1:0"
    }
    return model_ids.get(model_name)

def generate_smithy_document(model_name, namespace, api_name, description, create_crud_operations, generate_docs, additional_context):
    model_id = resolve_model_id(model_name)
    if not model_id:
        raise ValueError(f"Unsupported model name: {model_name}")

    client = boto3.client("bedrock-runtime", region_name="us-west-2")

    prompt = (
        f"Generate a Smithy IDL document for the API in the namespace '{namespace}' named '{api_name}' with the following description: '{description}'. "
        f"The API should be RESTful and use the HTTP protocol."
        f"The operations should be attached using the create, read, update, list, and delete operations off of a resource that is named based on the api"
        f"Additional context: {additional_context}. "
        f"{'Include CRUD operations.' if create_crud_operations else ''} "
        f"{'Generate documentation for each operation using the @documentation attribute.' if generate_docs else ''} "
        f"Each operation should have a Request and Response object that end in Request and Response."
    )

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10000,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    request = json.dumps(native_request)

    response = client.invoke_model(modelId=model_id, body=request)

    model_response = json.loads(response["body"].read())

    response_text = model_response["content"][0]["text"]
    return response_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Smithy document using AWS Bedrock Messages API.")
    parser.add_argument('--model-name', type=str, required=True, choices=['haiku', 'sonnet'], help='The model to use (haiku or sonnet).')
    parser.add_argument('--namespace', type=str, required=True, help='The namespace for the Smithy API.')
    parser.add_argument('--api-name', type=str, required=True, help='The name of the API.')
    parser.add_argument('--description', type=str, required=True, help='The description of the API.')
    parser.add_argument('--create-crud-operations', type=bool, required=True, help='Whether to create CRUD operations (True or False).')
    parser.add_argument('--generate-docs', type=bool, required=True, help='Whether to generate documentation (True or False).')
    parser.add_argument('--additional-context', type=str, required=True, help='Additional context for the API.')
    parser.add_argument('--output-file', type=str, default='model.smithy', help='The file to write the output to (default: model.smithy).')

    args = parser.parse_args()

    # Generate the Smithy document
    smithy_document = generate_smithy_document(
        args.model_name,
        args.namespace,
        args.api_name,
        args.description,
        args.create_crud_operations,
        args.generate_docs,
        args.additional_context
    )

    # Write the Smithy document to the output file
    with open(args.output_file, 'w') as file:
        file.write(smithy_document)

    print(f"Smithy document written to {args.output_file}")