import json
import os
import uuid
import boto3
import zipfile
import tempfile
from git import Repo
from cookiecutter.main import cookiecutter
import requests
import shutil

s3_client = boto3.client('s3')

def list_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

def clean_openapi_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def download_file_as_raw(file_location):
    if "github.com" in file_location and "blob" in file_location:
        file_location = file_location.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return requests.get(file_location)

def handler(event, context):
    files = event['files']
    template = event['template']
    repo_url = template['repo']
    subdir = template.get('subDir', '')
    template_config = template['config']
    target_s3 = template['target']
    app_name = template_config.get('app_name', 'default_app')

    working_dir = tempfile.mkdtemp()

    run_uuid = str(uuid.uuid4())
    cookiecutter_output_path = os.path.join(working_dir, run_uuid)
    os.makedirs(cookiecutter_output_path)

    repo_dir = os.path.join(working_dir, 'repo')
    Repo.clone_from(repo_url, repo_dir)

    if subdir:
        template_path = os.path.join(repo_dir, subdir)
    else:
        template_path = repo_dir

    all_files_in_template = list_files(template_path)
    print(f"Files in the template directory after cloning: {all_files_in_template}")

    config_file_path = 'config.yaml'

    print(f"Config: {template_config}")

    cookiecutter(
        template_path,
        no_input=True,
        extra_context=template_config,
        output_dir=cookiecutter_output_path,
        config_file=config_file_path
    )

    openapi_dir = os.path.join(cookiecutter_output_path, app_name, 'src', 'main', 'openapi')
    clean_openapi_directory(openapi_dir)

    for file_info in files:
        file_path = file_info['path']
        file_location = file_info['location']

        destination_path = os.path.join(cookiecutter_output_path, app_name, file_path.lstrip('/'))
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        response = download_file_as_raw(file_location)

        if response.status_code == 200:
            with open(destination_path, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception(f"Failed to download file from {file_location}")

    zip_path = os.path.join(working_dir, f'{run_uuid}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(cookiecutter_output_path):
            for file in files:
                file_full_path = os.path.join(root, file)
                zipf.write(file_full_path, os.path.relpath(file_full_path, cookiecutter_output_path))

    s3_bucket = target_s3.split('//')[1].split('/')[0]
    s3_key = '/'.join(target_s3.split('//')[1].split('/')[1:]) + f'{run_uuid}.zip'

    with open(zip_path, 'rb') as f:
        s3_client.upload_fileobj(f, s3_bucket, s3_key)

    return {
        'statusCode': 200,
        'body': json.dumps(f'Uploaded to s3://{s3_bucket}/{s3_key}')
    }
