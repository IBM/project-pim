#!/bin/bash

set -x

[ -f /etc/pim/tritonserver.conf ] || touch /etc/pim/tritonserver.conf

# List of AI applications to be served from tritonserver
ai_apps=("fraud")

for app in "${ai_apps[@]}"; do
    mkdir -p /var/models/model_repository/${app}/1

    ONNX_MODEL_SOURCE=$(jq -r '.modelSource' /etc/pim/pim_config.json)
    if [[ -n "$ONNX_MODEL_SOURCE" ]]; then
    curl "$ONNX_MODEL_SOURCE" --output /var/models/model_repository/${app}/1/model.onnx
    fi

    CONFIG_FILE=$(jq -r '.configSource' /etc/pim/pim_config.json)
    if [[ -n "$CONFIG_FILE" ]]; then
        curl "$CONFIG_FILE" --output /var/models/model_repository/${app}/config.pbtxt
    fi
done

var_to_add=MODEL_REPOSITORY=/var/models/model_repository
sed -i "/^MODEL_REPOSITORY=.*/d"  /etc/pim/tritonserver.conf && echo "$var_to_add" >> /etc/pim/tritonserver.conf
