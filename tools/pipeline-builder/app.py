from aws_cdk import App
from pipeline_builder_stack import PipelineBuilderStack

app = App()
PipelineBuilderStack(app, "PipelineBuilderStack")
app.synth()