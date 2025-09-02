import argparse
import json
import logging
import os
import requests
import tarfile

from urllib.parse import urlparse

LOG_LEVEL = logging.INFO


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

logger = get_logger("download-manager")


def http_server(url, download_path):
    path = urlparse(url).path
    file_name = os.path.basename(path)
    file_path = f"{download_path}/{file_name}"
    
    if os.path.exists(file_path):
        logger.info(f"Skipping download of file as it is already present in the '{download_path}' the path")
    else:
        download_file_from_url(url, file_path)
    extract_tar_file(file_path, download_path)
    remove_tar_file(file_path)


def download_file_from_url(url, file_path):
    logger.info(f"Downloading file from the url '{url}'")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"File downloaded successfully to '{file_path}'")
    except requests.exceptions.RequestException as e:
        logger.error(f"error during download: {e}")


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
    
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        download_manager(config, args.downloadPath)
    except Exception as e:
        logger.error(f"error encountered: {e}")


if __name__ == "__main__":
    main()
