#!/bin/bash

if [ "$#" -eq 0 ]; then
  echo "Error: No application name provided"
  exit 1
fi

app=$1

# clone the source code
git clone https://github.com/PDeXchange/ai-demos/
cd ai-demos/

echo "find the app directory"
app_dir=$(find . -maxdepth 1 -type d -iname "*$app*" | head -n 1)
echo "app dir: $app_dir"
if [ -d "$app_dir" ]; then
    cd "$app_dir" || return
fi

echo "Build build_env container image"
# Build container image for the app
podman build . -t localhost/build_env

mkdir -p $(pwd)/model_repository
echo "Train the model using build_env container"
# Run the app image to generate the model file
podman run --rm  --name $app -v $(pwd):/app:Z -v $(pwd)/model_repository:/app/model_repository \
        --entrypoint="/bin/sh" localhost/build_env -c "cd /app && make train && make prepare"

echo "Model has been trained successfuly and available at: $(pwd)/model_repository/fraud/1"
exit 0
