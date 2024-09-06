#!/bin/bash

# Define the path to the JSON file
json_file="env-vars.json"

# Check if the JSON file exists
if [[ ! -f "$json_file" ]]; then
  echo "JSON file '$json_file' not found!"
  exit 1
fi

# Read variables from the JSON file using jq
export COMMIT_TYPE=$(jq -r '.COMMIT_TYPE' "$json_file")
export COMMIT_SCOPE=$(jq -r '.COMMIT_SCOPE' "$json_file")
export COMMIT_SUBJECT=$(jq -r '.COMMIT_SUBJECT' "$json_file")
export COMMIT_BODY=$(jq -r '.COMMIT_BODY' "$json_file")
export COMMIT_FOOTER=$(jq -r '.COMMIT_FOOTER' "$json_file")

# Verify that the variables are set
echo "COMMIT_TYPE=$COMMIT_TYPE"
echo "COMMIT_SCOPE=$COMMIT_SCOPE"
echo "COMMIT_SUBJECT=$COMMIT_SUBJECT"
echo "COMMIT_BODY=$COMMIT_BODY"
echo "COMMIT_FOOTER=$COMMIT_FOOTER"
