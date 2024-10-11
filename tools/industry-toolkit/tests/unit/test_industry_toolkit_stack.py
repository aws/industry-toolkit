import aws_cdk as core
import aws_cdk.assertions as assertions

from industry_toolkit.industry_toolkit_stack import IndustryToolkitStack

# example tests. To run these tests, uncomment this file along with the example
# resource in industry_toolkit/industry_toolkit_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = IndustryToolkitStack(app, "industry-toolkit")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
