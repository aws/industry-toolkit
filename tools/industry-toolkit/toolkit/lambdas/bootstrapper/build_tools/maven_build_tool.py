import xml.etree.ElementTree as ET
import os
from .build_tool import BuildTool

class MavenBuildTool(BuildTool):
    def write_config_files(self, app_dir: str):
        ecr_registry_uri = os.environ.get("ECR_REGISTRY_URI")
        if not ecr_registry_uri:
            raise ValueError("ECR_REGISTRY_URI environment variable is not set.")

        # Path to the pom.xml file
        pom_path = os.path.join(app_dir, "pom.xml")

        # Add Jib plugin to pom.xml
        self.add_jib_plugin_to_pom(pom_path, ecr_registry_uri)

    def add_jib_plugin_to_pom(self, pom_path, ecr_registry_uri):
        # Parse the pom.xml file
        tree = ET.parse(pom_path)
        root = tree.getroot()

        # Define namespaces for finding existing elements
        ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}

        # Find or create the <build> element
        build = root.find("mvn:build", ns)
        if build is None:
            build = ET.SubElement(root, "{http://maven.apache.org/POM/4.0.0}build")

        # Find or create the <plugins> element
        plugins = build.find("mvn:plugins", ns)
        if plugins is None:
            plugins = ET.SubElement(build, "{http://maven.apache.org/POM/4.0.0}plugins")

        # Check if jib plugin is already present
        jib_plugin = next((plugin for plugin in plugins.findall("mvn:plugin", ns)
                           if plugin.find("mvn:artifactId", ns).text == "jib-maven-plugin"), None)
        if jib_plugin is None:
            # Add the jib-maven-plugin configuration
            jib_plugin = ET.SubElement(plugins, "{http://maven.apache.org/POM/4.0.0}plugin")
            ET.SubElement(jib_plugin, "{http://maven.apache.org/POM/4.0.0}groupId").text = "com.google.cloud.tools"
            ET.SubElement(jib_plugin, "{http://maven.apache.org/POM/4.0.0}artifactId").text = "jib-maven-plugin"
            ET.SubElement(jib_plugin, "{http://maven.apache.org/POM/4.0.0}version").text = "3.1.4"

            # Add configuration for ECR
            configuration = ET.SubElement(jib_plugin, "{http://maven.apache.org/POM/4.0.0}configuration")

            # Configure output to ECR
            to = ET.SubElement(configuration, "{http://maven.apache.org/POM/4.0.0}to")
            ET.SubElement(to, "{http://maven.apache.org/POM/4.0.0}image").text = f"{ecr_registry_uri}:latest"

            # Set ECR authentication
            auth = ET.SubElement(to, "{http://maven.apache.org/POM/4.0.0}auth")
            ET.SubElement(auth, "{http://maven.apache.org/POM/4.0.0}username").text = "AWS"
            ET.SubElement(auth, "{http://maven.apache.org/POM/4.0.0}password").text = "${env.ECR_LOGIN_PASSWORD}"

        # Remove namespace prefixes before saving
        self._remove_namespaces(root)
        tree.write(pom_path, encoding="UTF-8", xml_declaration=True)
        print(f"Added jib-maven-plugin to {pom_path}")

    def _remove_namespaces(self, element):
        """Recursively remove namespaces from XML elements."""
        for elem in element.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]  # Remove namespace
