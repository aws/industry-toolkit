name: Build and Publish Docker Image to ECR

on:
  push:
    paths:
      - 'tools/bootstrapper-base-image/**'
    branches:
      - main
  workflow_dispatch:

jobs:
  build-and-publish:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Log in to Amazon ECR Public
        run: |
          export AWS_ECR_LOGIN=$(aws ecr-public get-login-password --region us-east-1)
          docker login -u AWS -p $AWS_ECR_LOGIN public.ecr.aws

      - name: Build Docker image
        run: |
          cd tools/bootstrapper-base-image
          docker build -t industry-toolkit-base-image:latest .

      - name: Tag Docker image for ECR
        run: |
          docker tag industry-toolkit-base-image:latest public.ecr.aws/m2c6h9n1/industry-toolkit/bootstrapper-base-image:latest

      - name: Push Docker image to ECR
        run: |
          docker push public.ecr.aws/m2c6h9n1/industry-toolkit/bootstrapper-base-image:latest
