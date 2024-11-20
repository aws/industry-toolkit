from infra.infra_generator import InfraGenerator

import os
import json
import shutil


class CloudFormationInfraGenerator(InfraGenerator):

    def generate_infra(self, project_id: str, infra_config: dict) -> str:
        project_dir = self.create_infra_dir(project_id)

        # Create config file dev.json
        self.write_config(infra_config, "dev.json")

        return self.copy_cloudformation_template(project_dir)

    def copy_cloudformation_template(self, project_dir: str) -> str:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        source_template_path = os.path.join(module_dir, 'templates', 'infra.ecs-fargate.template')
        destination_template_path = os.path.join(project_dir, "infra.yaml")

        shutil.copyfile(source_template_path, destination_template_path)

        return destination_template_path

    def write_config(self, params, filename='dev.json'):
        cfn_params = {
            "Parameters": {
                "imageUri": "PLACEHOLDER_URI"
            }
        }

        cfn_params["Parameters"].update(params)

        try:
            with open(filename, 'w') as json_file:
                json.dump(cfn_params, json_file, indent=2)
            print(f"Successfully wrote CloudFormation parameters to {filename}")
        except IOError as e:
            print(f"An error occurred while writing to the file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
