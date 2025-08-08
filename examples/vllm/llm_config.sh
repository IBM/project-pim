#!/bin/bash

set -x

[ -f /etc/pim/llm.conf ] || touch /etc/pim/llm.conf

# Reads comma separated env values from llmEnv var in pim_config.json and loads it in separate lines in llm.conf to be consumed by vLLM application
LLM_ENV=$(jq -r '.llmEnv' /etc/pim/pim_config.json)
IFS=',' read -ra envs <<< "$LLM_ENV"
for env in "${envs[@]}"; do
    key="${env%%=*}"
    key="$(echo "$key" | sed 's/^[[:space:]]*//')"
    sed -i "/^${key}=.*/d" /etc/pim/llm.conf && echo "$(echo "$env" | sed 's/^[[:space:]]*//')" >> /etc/pim/llm.conf
done


var_to_add=LLM_ARGS=$(jq -r '.llmArgs' /etc/pim/pim_config.json)
sed -i "/^LLM_ARGS=.*/d" /etc/pim/llm.conf && echo "$var_to_add" >> /etc/pim/llm.conf

var_to_add=LLM_IMAGE=$(jq -r '.llmImage' /etc/pim/pim_config.json)
sed -i "/^LLM_IMAGE=.*/d" /etc/pim/llm.conf && echo "$var_to_add" >> /etc/pim/llm.conf

# Creating and using cache dir to store models offline so when the application reloads it pulls model from the cache dir
mkdir /var/huggingface
var_to_add=HF_HUB_CACHE=/var/huggingface
sed -i "/^HF_HUB_CACHE=.*/d" /etc/pim/llm.conf && echo "$var_to_add" >> /etc/pim/llm.conf

MODEL="granite-3.2-8b-instruct.tar.gz"
MODEL_DIR="/var/huggingface"
URL="http://9.114.99.184/$MODEL"
OUTPUT="$MODEL_DIR/$MODEL"
RETRIES=3
WAIT_SECONDS=10

attempt=1
while [ $attempt -le $RETRIES ]; do
    echo "Attempt $attempt to download $URL..."
    curl -fSL -o "$OUTPUT" "$URL"
    if [ $? -eq 0 ]; then
        echo "Download succeeded."
        break
    else
        echo "Download failed. Retrying in $WAIT_SECONDS seconds..."
        sleep $WAIT_SECONDS
        attempt=$((attempt + 1))
    fi
done

if [ ! -f "$OUTPUT" ]; then
    echo "Failed to download the file after $RETRIES attempts. Exiting."
    exit 1
fi

sleep 5
# Extract only if the file exists and curl succeeded
tar -xzvf "$OUTPUT" --one-top-level -C "$MODEL_DIR"

