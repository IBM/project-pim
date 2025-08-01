#!/bin/bash

set -x

[ -f /etc/pim/hmc.conf] || touch /etc/pim/hmc.conf

var_to_add=MODEL_PARAM=$(jq -r '.llmArgs' /etc/pim/pim_config.json | awk '{print $2}')
sed -i "/^MODEL_PARAM=.*/d" /etc/pim/hmc.conf && echo "$var_to_add" >> /etc/pim/hmc.conf

# Reads comma separated env values from hmcConfig var in pim_config.json and loads them into separate lines in hmc.conf to be consumed by agentic AI application
HMC_CONFIGS=$(jq -r '.hmcConfig' /etc/pim/pim_config.json)
IFS=',' read -ra envs <<< "$HMC_CONFIGS"
for env in "${envs[@]}"; do
    key="${env%%=*}"
    key="$(echo "$key" | sed 's/^[[:space:]]*//')"
    sed -i "/^${key}=.*/d" /etc/pim/hmc.conf && echo "$(echo "$env" | sed 's/^[[:space:]]*//')" >> /etc/pim/hmc.conf
done
