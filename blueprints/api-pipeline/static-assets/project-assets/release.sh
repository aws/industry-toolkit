set -euo pipefail

echo "Getting credentials..."
MI=`curl $AWS_CONTAINER_TOKEN_ENDPOINT`
ACCESS_KEY_ID=$(echo "$MI" | jq -r '.AccessKeyId')
SECRET_ACCESS_KEY=$(echo "$MI" | jq -r '.SecretAccessKey')
ORIGINAL_REMOTE=`git config --get remote.origin.url`
SOURCE_REPO_URL=`sed -e "s^//^//$ACCESS_KEY_ID:$SECRET_ACCESS_KEY@^" <<< $ORIGINAL_REMOTE`
echo $SOURCE_REPO_URL

echo "Configuring git..."
git remote set-url origin $SOURCE_REPO_URL
git config --global user.email "noreply@amazon.com"
git config --global user.name "Release Workflow"

if git tag | grep '.'; then
  latest_tag=$(git describe --tags `git rev-list --tags --max-count=1`)
  echo "Previous version is $latest_tag."
  # SemVer format, but strip any 'v' or 'V' from the beginning.
  IFS='.' read -r -a version_parts <<< "${latest_tag//[vV]/}"

  # Increment the patch version
  patch=$((version_parts[2] + 1))

  version="${version_parts[0]}.${version_parts[1]}.$patch"
  echo "New version is $version."
else
  echo "No existing git tags, setting version to 1.0.0."
  version="1.0.0"
fi

echo "Injecting $version into smithy-build.json..."
jq --arg version "$version" '
  if .plugins["java-client-codegen"] then
    .plugins["java-client-codegen"].moduleVersion = $version
  else
    .
  end |
  if .plugins["typescript-client-codegen"] then
    .plugins["typescript-client-codegen"].packageVersion = $version
  else
    .
  end
' smithy-build.json > smithy-build.tmp && mv smithy-build.tmp smithy-build.json

echo "Using the following smithy-build.json file..."
cat smithy-build.json

chmod +x gradlew
./gradlew clean publish -Pversion=$version

git tag -a "$version" -m "Release $version"
git push origin $version

echo $version > version