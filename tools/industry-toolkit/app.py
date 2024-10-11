#!/usr/bin/env python3
import aws_cdk as cdk
from toolkit.stack import IndustryToolkitStack

app = cdk.App()

# Instantiate the IndustryToolkitStack
IndustryToolkitStack(app, "IndustryToolkitStack")

# Synthesize the application
app.synth()
