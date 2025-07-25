#!/bin/bash

set -x

[ -f /etc/pim/hmc_agent.conf] || touch /etc/pim/hmc_agent.conf

var_to_add=OLLAMA_MODEL=$(jq -r '.llmArgs' /etc/pim/pim_config.json | awk '{print $2}')
sed -i "/^OLLAMA_MODEL=.*/d" /etc/pim/hmc_agent.conf && echo "$var_to_add" >> /etc/pim/hmc_agent.conf

# Read HMC IP address, username and password from /etc/pim/hmc.cfg, Populate them to /etc/pim/hmc_agent.conf
var_to_add=HMC_IP=$(grep -r "HMC_IP" /etc/pim/pim_config.json | awk '{print $2}')
sed -i "/^HMC_IP=.*/d" /etc/pim/hmc_agent.conf && echo "$var_to_add" >> /etc/pim/hmc_agent.conf

var_to_add=HMC_USERNAME=$(grep -r "HMC_USERNAME" /etc/pim/pim_config.json | awk '{print $2}')
sed -i "/^HMC_USERNAME=.*/d" /etc/pim/hmc_agent.conf && echo "$var_to_add" >> /etc/pim/hmc_agent.conf

var_to_add=HMC_PASSWORD=$(grep -r "HMC_PASSWORD" /etc/pim/pim_config.json | awk '{print $2}')
sed -i "/^HMC_PASSWORD=.*/d" /etc/pim/hmc_agent.conf && echo "$var_to_add" >> /etc/pim/hmc_agent.conf
