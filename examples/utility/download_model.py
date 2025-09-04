import argparse
import hashlib
import json
import logging
import os
import requests
import tarfile

from urllib.parse import urlparse

logger = None

def get_logger(name, log_level):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-18s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def http_server(url, download_path):
    path = urlparse(url).path
    file_name = os.path.basename(path)
    file_path = f"{download_path}/{file_name}"
    
    if os.path.exists(file_path):
        logger.info(f"Skipping download of file as it is already present in the '{download_path}' the path")
    else:
        checksum = get_tarfile_checksum(url)
        download_file_from_url(url, file_path, checksum)
    extract_tar_file(file_path, download_path)
    remove_tar_file(file_path)


def get_tarfile_checksum(url):
    url_path = urlparse(url).path
    tar_file = url_path.split('/')[-1]
    checksum_file = tar_file.replace('.tar.gz', '.checksum')
    checksum_url = url.replace(tar_file, checksum_file)

    try:
        response = requests.get(checksum_url)
        response.raise_for_status()
        checksum_value = response.text.strip().split()[0]
    except Exception as e:
        logger.error(f"failed to get checksum value: {e}")
        raise e
    return checksum_value


def download_file_from_url(url, file_path, checksum):
    logger.info(f"Downloading file from the url '{url}'")

    try:
        response = requests.get(url, stream=True)
        digest = hashlib.sha256()
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                digest.update(chunk)
        logger.info(f"File downloaded successfully to '{file_path}'")
        file_checksum = digest.hexdigest()
        if checksum == file_checksum:
            logger.debug("Integrity of the downloaded file validated.")
        else:
            logger.error(f"Mismatch in the checksum value.\nExpected: {checksum}.\nGot: {file_checksum}")
            raise Exception("Mismatch in the checksum value")
    except requests.exceptions.RequestException as e:
        logger.error(f"error during download: {e}")
        raise e


def extract_tar_file(file_path, extract_path):
    try:
        with tarfile.open(file_path, "r:gz") as tar:
            tar.extractall(extract_path)
        logger.info(f"File extracted at the location: {extract_path}")
    except Exception as e:
        logger.error(f"failed to untar '{file_path}', error: {e}")
        raise e


def remove_tar_file(file_path):
    try:
        logger.info(f"Deleting {file_path} file.")
        os.remove(file_path)
        logger.info(F"File {file_path} deleted.")
    except Exception as e:
        logger.error(f"failed to remove '{file_path}' file. error: {e}")
        raise e


def load_config(config_path):
    with open(config_path, "r") as config_file:
        return json.load(config_file)


def download_manager(config, download_path):
    if "modelSource" in config:
        logger.info("Starting model download process.")
        http_server(config["modelSource"]["url"], download_path)
        logger.info("Model download process completed.")
    else:
        logger.info("Source to download model is not specified.")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", type=str, help="Path to the configuration file")
    parser.add_argument("--downloadPath", type=str, help="Download path of the the AI model.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    
    global logger
    logger = get_logger("download-manager", log_level)
    
    try:
        config = load_config(args.config)
        download_manager(config, args.downloadPath)
    except Exception as e:
        logger.error(f"error encountered: {e}")


if __name__ == "__main__":
    main()
