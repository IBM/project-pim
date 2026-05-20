#!/bin/bash

# Create .profile and set binaries path
touch $HOME/.profile

echo 'PATH=/QOpenSys/pkgs/bin:$PATH' >> $HOME/.profile
echo 'export PATH' >> $HOME/.profile
. $HOME/.profile

# Install system dependencies (base tools + Python packages that work)
# Install GCC 10 for building lxml with Python 3.13 (see: https://github.com/IBM/ibmi-oss-issues/issues/27#issuecomment-1403734128)
yum install -y git \
    gcc10 \
    gcc10-cplusplus \
    libxml2 \
    libxml2-devel \
    libxslt \
    libxslt-devel \
    zlib \
    zlib-devel \
    openssl \
    openssl-devel \
    openssh \
    python3.13 \
    python3.13-pip \
    python3.13-devel \
    python3.13-cffi \
    python3.13-cryptography \
    python3.13-bcrypt \
    python3.13-paramiko \
    python3.13-six

# Create virtual environment for Python 3.13 with access to system packages
# --system-site-packages allows venv to use yum-installed packages like cryptography
python3.13 -m venv --system-site-packages $HOME/pim-venv

# Use venv's pip directly without activation (avoids shell compatibility issues)
$HOME/pim-venv/bin/pip install --upgrade pip

# Set GCC 10 as the compiler for building lxml (required for Python 3.13)
export CC=/QOpenSys/pkgs/bin/gcc-10
export CXX=/QOpenSys/pkgs/bin/g++-10

# Verify GCC version
$CC --version

# Set linker flags and library paths for 64-bit libs ONLY
# Use -Wl,-L to force linker to search /QOpenSys/pkgs/lib first
export LDFLAGS="-L/QOpenSys/pkgs/lib -Wl,-L/QOpenSys/pkgs/lib -Wl,-blibpath:/QOpenSys/pkgs/lib"
export LIBPATH="/QOpenSys/pkgs/lib"
export CFLAGS="-maix64"
export CXXFLAGS="-maix64"
export OBJECT_MODE=64

# Install lxml (will be built from source with GCC 10)
$HOME/pim-venv/bin/pip install lxml==6.1.0 --no-cache-dir

# Install other pip dependencies (yum already has paramiko, cryptography, bcrypt, cffi, six)    
# Use --no-deps to avoid dependency conflicts with yum packages
$HOME/pim-venv/bin/pip install --no-cache-dir --no-deps \
    bs4 \
    beautifulsoup4 \
    urllib3 \
    configobj \
    requests \
    certifi \
    charset-normalizer \
    idna \
    Jinja2 \
    MarkupSafe \
    soupsieve \
    typing-extensions \
    pycparser \
    pynacl

# Install schily to generate cloudinit
yum-config-manager --add-repo http://www.the-i-doctor.com/oss/repo/the-i-doctor.repo
yum install -y schily-tools
echo 'PATH=$PATH:/opt/schily/bin' >> $HOME/.profile
echo 'export PATH' >> $HOME/.profile

mkdir -p source
cd source

# Clone source code from github repo
curl "https://codeload.github.com/IBM/project-pim/zip/refs/heads/main" --output pim.zip
unzip pim.zip
cd project-pim-main
export PYTHONPATH=.
