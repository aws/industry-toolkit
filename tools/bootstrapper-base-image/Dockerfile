FROM public.ecr.aws/lambda/python:3.12

ENV JAVA_HOME=/usr/lib/jvm/java-17-amazon-corretto
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN curl -L https://corretto.aws/downloads/latest/amazon-corretto-17-x64-linux-jdk.tar.gz -o corretto.tar.gz && \
    mkdir -p /usr/lib/jvm && \
    tar -xzf corretto.tar.gz -C /usr/lib/jvm && \
    mv /usr/lib/jvm/amazon-corretto-17* /usr/lib/jvm/java-17-amazon-corretto && \
    rm corretto.tar.gz

ENV OPENAPI_GENERATOR_CLI_VERSION=7.9.0
ENV OPENAPI_GENERATOR_CLI_JAR=/opt/openapi-generator-cli.jar

RUN curl -L https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/$OPENAPI_GENERATOR_CLI_VERSION/openapi-generator-cli-$OPENAPI_GENERATOR_CLI_VERSION.jar \
    -o $OPENAPI_GENERATOR_CLI_JAR

ENV PATH="${PATH}:/opt"
