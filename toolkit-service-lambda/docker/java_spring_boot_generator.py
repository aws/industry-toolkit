from docker.dockerfile_generator import DockerfileGenerator


class JavaSpringBootDockerfileGenerator(DockerfileGenerator):

    def generate_dockerfile(self, project_id: str) -> str:
        base_image = 'public.ecr.aws/amazonlinux/amazonlinux:latest'
        jar_file = 'app.jar'

        dockerfile_content = f"""
FROM {base_image}

RUN yum update -y && \
yum install -y java-17-amazon-corretto-headless && \
yum clean all

WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]

COPY target/*.jar /app/app.jar
"""

        return self.write_dockerfile(project_id, dockerfile_content.strip())
