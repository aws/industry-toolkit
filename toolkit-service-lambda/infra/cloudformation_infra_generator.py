from infra.infra_generator import InfraGenerator
import os
import shutil

class CloudFormationInfraGenerator(InfraGenerator):

    def generate_infra(self, project_id: str, config: dict) -> str:
        project_dir = self.create_infra_dir(project_id)
        return self.copy_cloudformation_template(project_id, project_dir, config)

    def copy_cloudformation_template(self, project_id: str, project_dir: str, config: dict) -> str:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        source_template_path = os.path.join(module_dir, 'templates', 'infra.ecs-fargate.template')
        destination_template_path = os.path.join(project_dir, "infra.yaml")

        shutil.copyfile(source_template_path, destination_template_path)

        return destination_template_path
