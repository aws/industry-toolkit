#!/bin/bash

echo Checking if a specific tag key exists

# Define the tag key to search for
TAG_KEY=$COMMIT_SCOPE

if [[ ! -f tags.json ]]; then
    echo Failed to create tags.json
    exit 1
fi

echo Tags JSON content
cat tags.json

# Use jq to get the value of the tag with the specific key
TAG_VALUE=$(jq -r --arg TAG_KEY $TAG_KEY '.tags[] | select(.key == $TAG_KEY) | .value' tags.json)

# Check if the tag key exists
if [[ -n $TAG_VALUE ]]; then
    echo Current version is:$TAG_VALUE

    # Extract the version parts
    IFS='.' read -r major minor patch <<< $TAG_VALUE

    # Determine version increment based on commit message
    if [[ "$COMMIT_FOOTER" == *"BREAKING CHANGE"* ]]; then
    ((major++))
    minor=0
    patch=0
    elif [[ $COMMIT_TYPE == feat ]]; then
    ((minor++))
    patch=0
    elif [[ $COMMIT_TYPE == fix ]]; then
    ((patch++))
    else
    echo No relevant changes found to update the version.
    exit 0
    fi

# Set new version number
SDK_VERSION=$major.$minor.$patch
echo Updated version is:$SDK_VERSION

else
    echo Tag key $TAG_KEY does not exist in the CodeArtifact repository.
    echo SDK version will default to '1.0.0'.
    SDK_VERSION=1.0.0
fi

# Use jq to create a JSON object and write it to a file
jq -n --arg key "$COMMIT_SCOPE" --arg value "$SDK_VERSION" \
  '{($key): $value}' > version.json

# Show the contents of the version.json file
cat version.json