import filecmp
import hashlib
import logging
import os
import subprocess
import paramiko
import time

from configobj import ConfigObj
from urllib.parse import urlparse
import cli.utils.string_util as util

LOG_LEVEL = logging.INFO

def getclidir():
    cwd = os.getcwd()
    cwd = f"{cwd}/cli"
    return cwd

clidir = getclidir()
PARTITION_FLAVOR_DIR = f"{clidir}/partition-flavor"
keys_path = clidir + "/keys"
iso_dir = clidir + "/iso"
update_iso_dir = clidir + "/update-iso"
cloud_init_config_dir =  clidir + "/cloud-init-iso/config"
cloud_init_update_config_dir =  clidir + "/cloud-init-iso/update-config"

def set_log_level(level):
    global LOG_LEVEL
    LOG_LEVEL = level


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-18s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger

logger = get_logger("utility")

def create_dir(path):
    try:
        if not os.path.isdir(path):
            os.mkdir(path)
    except OSError as e:
        logger.error(f"failed to create '{path}' directory, error: {e}")
        raise


def file_checksum(file):
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * sha256.block_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def string_hash(str):
    return hashlib.sha256(str.encode('utf-8')).hexdigest()


def readfile(filename):
    f = open(filename, "r")
    data = f.read()
    return data


def verify_checksum(file, checksum_file):
    file_sha256 = file_checksum(file)
    data = readfile(checksum_file)
    csum = data.split(' ')[0]
    if csum == file_sha256:
        return True
    return False


def get_iso_url_and_checksum_path(config, iso_dir):
    iso_url = util.get_bootstrap_iso_download_url(config)
    iso_file_path = f"{iso_dir}/{util.get_bootstrap_iso(config)}"
    url_path = urlparse(iso_url).path
    iso_file = url_path.split('/')[-1]
    checksum_file = iso_file.replace('.iso', '.checksum')
    checksum_url = iso_url.replace(iso_file, checksum_file)
    checksum_file_path = f"{iso_dir}/{checksum_file}"
    return iso_url, iso_file_path, checksum_url, checksum_file_path


def load_partition_flavor(flavor_name):
    try:
        flavor_list = list_defined_partition_flavor()
        file_name = f"{flavor_name}.ini"
        if flavor_name in flavor_list:
            config = ConfigObj(f"{PARTITION_FLAVOR_DIR}/{file_name}")
            return config
        raise Exception(
            f"partition flavor with name '{flavor_name}' is undefined")
    except Exception as e:
        raise e


def list_defined_partition_flavor():
    flavor_list = []
    try:
        config_list = os.listdir(PARTITION_FLAVOR_DIR)
        for file in config_list:
            name = file.split(".")[0]
            flavor_list.append(name)
    except Exception as e:
        raise e
    return flavor_list


logger = get_logger("common-utils")


def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return client


def ssh_to_partition(config):
    ip = util.get_ip_address(config)
    username = util.get_ssh_username(config)
    ssh_key = util.get_ssh_priv_key(config)
    for i in range(50):
        scp_port = 22
        client = get_ssh_client()
        try:
            client.connect(ip, scp_port, username,
                           key_filename=ssh_key, timeout=10)
            break
        except Exception as e:
            if i == 49:
                logger.error(
                    f"failed to establish SSH connection to partition after 50 retries, error: {e}")
                raise paramiko.SSHException(
                    f"failed to establish SSH connection to partition after 50 retries, error: {e}")
            logger.debug("Not able to SSH to the partition yet, retrying..")
            time.sleep(10)
    return client


def create_dir(path):
    try:
        if not os.path.isdir(path):
            os.mkdir(path)
    except OSError as e:
        logger.error(f"failed to create '{path}' directory, error: {e}")
        raise


def initialize_config(config_file_path):
    try:
        config = ConfigObj(config_file_path)
        if util.has_custom_flavor(config):
            config["partition-flavor"] = config["custom-flavor"]
        else:
            flavor_name = util.get_partition_flavor(config)
            config["partition-flavor"] = load_partition_flavor(flavor_name)
    except Exception as e:
        logger.error(f"failed to parse {config_file_path}, error: {e}")
        raise e
    return config


def check_if_keys_generated(config):
    priv_key = f"{keys_path}/{util.get_partition_name(config)}_pim"
    pub_key = f"{keys_path}/{util.get_partition_name(config)}_pim.pub"
    if os.path.isfile(priv_key) and os.path.isfile(pub_key):
        return True
    return False


def load_ssh_config(config):
    config["ssh"]["user-name"] = "pim"
    config["ssh"]["priv-key-file"] = keys_path + "/" + \
        util.get_partition_name(config).lower() + "_pim"
    config["ssh"]["pub-key-file"] = keys_path + "/" + \
        util.get_partition_name(config).lower() + "_pim.pub"
    return config


def generate_ssh_keys(config):
    create_dir(keys_path)
    key_name = f"{keys_path}/{util.get_partition_name(config).lower()}_pim"
    cmd = f"ssh-keygen -b 4096 -t rsa -m PEM -f {key_name} -q -N \"\""
    result = subprocess.run(
        cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        logger.error(
            f"failed to run ssh-keygen command to generate keypair, error: {result.stderr} \n {result.stdout}")
        raise Exception(
            f"failed to run ssh-keygen command to generate keypair, error: {result.stderr}")
    logger.debug("SSH keypair generated successfully")

# Compares dir1 & dir2 and returns True if there is a difference(either new files introduced in dir2 or changes in file contents between the two dirs)
def compare_dir(dir1, dir2):
    dir_comp = filecmp.dircmp(dir1, dir2)
    if len(dir_comp.right_only) > 0 or len(dir_comp.diff_files) > 0:
        return True
    return False

def load_ssh_keys(config):
    if not check_if_keys_generated(config):
        generate_ssh_keys(config)
    config = load_ssh_config(config)
    return config
