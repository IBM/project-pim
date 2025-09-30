#!/bin/bash

set -x

mkdir -p /etc/pim/models

MODEL=$(jq -r '.model' /etc/pim/pim_config.json)
curl "$MODEL" --output /etc/pim/models/model.h5

MAPPER=$(jq -r '.mapper' /etc/pim/pim_config.json)
curl "$MAPPER" --output /etc/pim/models/fitted_mapper.pkl
