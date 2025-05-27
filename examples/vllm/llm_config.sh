#!/bin/bash

set -x

[ -f /etc/pim/llm.conf ] || touch /etc/pim/llm.conf

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

mkdir /var/huggingface
var_to_add=HF_HUB_CACHE=/var/huggingface
sed -i "/^HF_HUB_CACHE=.*/d" /etc/pim/llm.conf && echo "$var_to_add" >> /etc/pim/llm.conf

