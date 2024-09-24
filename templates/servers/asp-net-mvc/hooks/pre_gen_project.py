import json
import os
import requests
import yaml

# Use the cookiecutter context to get the correct template directory
template_root_dir = os.getenv('COOKIECUTTER_TEMPLATE_DIR')

if not template_root_dir:
    raise RuntimeError("Could not find the template directory from environment variables.")

# Path to the cookiecutter.json file in the template root directory
cookiecutter_file = os.path.join(template_root_dir, "cookiecutter.json")

# Ensure the cookiecutter.json file exists
if not os.path.exists(cookiecutter_file):
    raise FileNotFoundError(f"cookiecutter.json file not found at {cookiecutter_file}")

# Load the cookiecutter.json content
with open(cookiecutter_file, "r") as f:
    config = json.load(f)

# Get the OpenAPI spec URL from the "openapi_spec_url" property
openapi_spec_url = config.get("openapi_spec_url")

if not openapi_spec_url:
    raise ValueError("The 'openapi_spec_url' property is missing in cookiecutter.json")

# Download the OpenAPI spec from the provided URL
response = requests.get(openapi_spec_url)

# Check if the request was successful
if response.status_code != 200:
    raise RuntimeError(f"Failed to download OpenAPI spec from {openapi_spec_url}. Status code: {response.status_code}")

# Save the OpenAPI spec locally (you can change the filename as needed)
openapi_spec_filename = "openapi_spec.yaml"
with open(openapi_spec_filename, "wb") as f:
    f.write(response.content)

print(f"OpenAPI spec downloaded and saved as {openapi_spec_filename}")

# Load the OpenAPI spec from the saved YAML file
with open(openapi_spec_filename, "r") as f:
    openapi_spec = yaml.safe_load(f)

# Function to generate a basic ASP.NET MVC controller from the OpenAPI spec
def generate_controller(openapi_spec):
    # Extract information from OpenAPI spec (basic structure)
    paths = openapi_spec.get("paths", {})
    controller_name = "ApiController"  # You can customize the controller name
    controller_methods = []

    for path, methods in paths.items():
        for method, details in methods.items():
            operation_id = details.get("operationId", method + path.replace("/", "_"))
            summary = details.get("summary", "No summary provided.")
            response = details.get("responses", {})
            
            # Generate a method signature
            method_signature = f"    public IActionResult {operation_id}()"
            method_body = f"        // TODO: Implement {summary}\n"

            # Generate responses handling (this can be enhanced)
            if response:
                for status_code, response_details in response.items():
                    method_body += f"        // Handle response for {status_code}\n"

            # Combine into the controller method
            controller_methods.append(f"{method_signature}\n{{\n{method_body}}}\n")

    # Combine the controller methods into a class definition
    controller_code = f"""using Microsoft.AspNetCore.Mvc;

namespace YourNamespace.Controllers
{{
    [ApiController]
    [Route("api/[controller]")]
    public class {controller_name} : ControllerBase
    {{
{"\n".join(controller_methods)}
    }}
}}
"""

    return controller_code

# Generate the controller code
controller_code = generate_controller(openapi_spec)

# Save the generated controller to a file
controller_filename = "ApiController.cs"  # You can customize the filename
with open(controller_filename, "w") as f:
    f.write(controller_code)

print(f"ASP.NET MVC Controller generated and saved as {controller_filename}")
