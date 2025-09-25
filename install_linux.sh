#!/bin/bash

dnf install -y python3-pip libxml2-devel libxslt-devel rust cargo python-devel libffi-devel mkisofs
dnf groupinstall -y "Development Tools"
pip install uv

# Clone source code from github repo
curl "https://codeload.github.com/IBM/project-pim/zip/refs/heads/main" --output pim.zip
unzip pim.zip
cd project-pim-main
export PYTHONPATH=.

uv venv
source .venv/bin/activate
uv sync
