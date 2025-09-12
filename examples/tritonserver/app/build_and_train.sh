#!/bin/bash

if [ "$#" -eq 0 ]; then
  echo "Error: No application name provided"
  exit 1
fi

app=$1

# clone the source code
git clone https://github.com/PDeXchange/ai-demos/
cd ai-demos/

app_dir=$(find . -maxdepth 1 -type d -iname "*$app*" | head -n 1)
if [ -d "$app_dir" ]; then
    cd "$app_dir" || echo "failed to find the app: $app"; return
fi

# Build container image for the app
podman build . -t localhost/$app

# Run the app image to generate the model file
podman run --rm --name fraud-analytics -v model_repository:/fraud_detection/model_repository localhost/$app

model_vol_path=$(podman volume inspect model_repository | grep "Mountpoint" | awk -F'"' '{print $4}'
model_path=$(find $model_vol_path -iname model.onnx)
echo "model file path: $model_path"

cp $model_path ./
