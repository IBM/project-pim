#!/bin/bash

set -x

[ -f /etc/pim/hmc_agent.conf] || touch /etc/pim/hmc_agent.conf

var_to_add=OLLAMA_MODEL=$(jq -r '.llmArgs' /etc/pim/pim_config.json | awk '{print $2}')
sed -i "/^OLLAMA_MODEL=.*/d" /etc/pim/hmc_agent.conf && echo "$var_to_add" >> /etc/pim/hmc_agent.conf

# Get HMC IP address, username and password. Populate them to /etc/pim/hmc_agent.conf
