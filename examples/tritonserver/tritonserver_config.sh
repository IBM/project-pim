#!/bin/bash

set -x

mkdir -p /etc/pim/models/fraud_detection

[ -f /etc/pim/fraud_detection.conf ] || touch /etc/pim/fraud_detection.conf

mkdir -p /var/models/fraud_detection
mkdir -p /var/models/fraud_detection/model_repository/fraud/1

ONNX_MODEL_SOURCE=$(jq -r '.modelSource' /etc/pim/pim_config.json)
# Download model from the http server
if [[ -n "$ONNX_MODEL_SOURCE" ]]; then
   curl "$ONNX_MODEL_SOURCE" --output /var/models/fraud_detection/model_repository/fraud/1/model.onnx
fi

CONFIG_FILE=$(jq -r '.configSource' /etc/pim/pim_config.json)
if [[ -n "$CONFIG_FILE" ]]; then
    curl "$CONFIG_FILE" --output /var/models/fraud_detection/model_repository/fraud/config.pbtxt
fi

var_to_add=MODEL_REPOSITORY=/var/models/fraud_detection/model_repository
sed -i "/^MODEL_REPOSITORY=.*/d"  /etc/pim/fraud_detection.conf && echo "$var_to_add" >> /etc/pim/fraud_detection.conf
