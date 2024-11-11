FROM public.ecr.aws/lambda/python:3.12

ENV OPENAPI_GENERATOR_CLI_VERSION=7.9.0
ENV OPENAPI_GENERATOR_CLI_JAR=/opt/openapi-generator-cli.jar

RUN microdnf install -y tar gzip java-17-amazon-corretto-headless git \
    && microdnf clean all

RUN curl -L https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/$OPENAPI_GENERATOR_CLI_VERSION/openapi-generator-cli-$OPENAPI_GENERATOR_CLI_VERSION.jar \
    -o $OPENAPI_GENERATOR_CLI_JAR

COPY requirements.txt .
RUN pip install -r requirements.txt
asdf
COPY . ${LAMBDA_TASK_ROOT}

CMD ["handler.lambda_handler"]
