#!/bin/bash

dnf install -y python3-pip libxml2-devel libxslt-devel python-devel libffi-devel mkisofs
dnf groupinstall -y "Development Tools"

# Install ISO creation tool
# Try mkisofs (older systems) or xorriso (preferred for newer systems)
# Note: xorriso package provides mkisofs compatibility wrapper automatically
dnf install -y mkisofs || dnf install -y xorriso

# Install Rust - try rust-toolset first, fallback to rust+cargo (older versions)
dnf install -y rust-toolset || dnf install -y rust cargo

# Upgrade pip to latest version
pip install --upgrade pip

pip install uv

# Clone source code from github repo
curl "https://codeload.github.com/IBM/project-pim/zip/refs/heads/main" --output pim.zip
unzip pim.zip
cd project-pim-main
export PYTHONPATH=.

uv venv
source .venv/bin/activate
uv sync
