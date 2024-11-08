FROM public.ecr.aws/lambda/python:3.12

RUN microdnf install -y tar gzip java-17-amazon-corretto-headless git && \
    microdnf clean all

ENV OPENAPI_GENERATOR_CLI_VERSION=7.9.0
ENV OPENAPI_GENERATOR_CLI_JAR=/opt/openapi-generator-cli.jar

RUN curl -L https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/$OPENAPI_GENERATOR_CLI_VERSION/openapi-generator-cli-$OPENAPI_GENERATOR_CLI_VERSION.jar \
    -o $OPENAPI_GENERATOR_CLI_JAR

ENV PATH="${PATH}:/opt"
