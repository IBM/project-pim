import json
import os
import requests
import subprocess

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

import cli.partition.activation as activation
import cli.partition.partition as partition
import cli.utils.common as common
import cli.utils.command_util as command_util
import cli.vios.vios as vios_operation

from cli.utils.string_util import *

logger = common.get_logger("iso")


def build_and_download_iso(config, slot_num, iso_dir, config_dir):
    common.create_dir(iso_dir)
    generate_cloud_init_iso_config(config, slot_num, config_dir)
    generate_cloud_init_iso_file(iso_dir, config, config_dir)
    download_bootstrap_iso(iso_dir, config)

def generate_cloud_init_iso_config(config, slot_num, config_dir):
    # Populate config object with slot_num
    config["partition"]["network"]["slot_num"] = slot_num
    file_loader = FileSystemLoader(f'{common.getclidir()}/cloud-init-iso/templates')
    env = Environment(loader=file_loader)

    network_config_template = env.get_template('99_custom_network.cfg')
    network_config_output = network_config_template.render(config=config)

    common.create_dir(config_dir)

    pim_config_json = config["ai"]["config-json"] if config["ai"]["config-json"] != "" else "{}"
    pim_config_json = json.loads(pim_config_json)

    # 'workloadImage' is being used inside the bootstrap iso to write the bootc image into disk, in case of modification of this field name, needs same modification in bootstrap.iso too.
    pim_config_json["workloadImage"] = get_workload_image(config)

    pim_config_file = open(config_dir + "/pim_config.json", "w")
    pim_config_file.write(json.dumps(pim_config_json))

    network_config_file = open(
        config_dir + "/99_custom_network.cfg", "w")
    network_config_file.write(network_config_output)

    auth_json = "{}" if config["ai"]["auth-json"] == "" else config["ai"]["auth-json"]
    auth_config_file = open(config_dir + "/auth.json", "w")
    auth_config_file.write(auth_json)
    logger.debug("Generated config files for the cloud-init ISO")


def generate_cloud_init_iso_file(iso_dir, config, config_dir):
    logger.debug("Generating cloud-init ISO file")
    cloud_init_image_name = get_cloud_init_iso(config)
    generate_cmd = f"mkisofs -l -o {iso_dir}/{cloud_init_image_name} {config_dir}"

    try:
        subprocess.run(generate_cmd.split(), check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(
            f"failed to generate cloud-init ISO via mkisofs, error: {e.stderr}")
        raise


def download_bootstrap_iso(iso_dir, config):
    iso_url, iso_file_path, checksum_url, checksum_file_path = common.get_iso_url_and_checksum_path(
        config, iso_dir)

    try:
        # Check if bootstrap iso is already downloaded locally(on IBMi)
        if os.path.isfile(iso_file_path):
            logger.debug(
                f"Bootstrap ISO '{iso_file_path}' found, checking integrity of the file")
            # Check if iso checksum file exists
            if not os.path.exists(checksum_file_path):
                # Download checksum file for bootstrap iso
                download_bootstrap_checksum(checksum_url, checksum_file_path)
            if not common.verify_checksum(iso_file_path, checksum_file_path):
                logger.debug(
                    "Bootstrap ISO checksum mismatch, cleaning up iso")
                cleanup_iso_artifacts(iso_file_path, checksum_file_path)
            else:
                logger.debug(
                    f"Integrity is matching, skipping bootstrap iso download..")
                return

        logger.debug("Downloading bootstrap ISO file...")

        response = requests.get(iso_url, stream=True)
        response.raise_for_status()

        with open(iso_file_path, "wb") as iso_file:
            for chunk in response.iter_content(chunk_size=8192):
                iso_file.write(chunk)

        # Download checksum file for bootstrap iso
        download_bootstrap_checksum(checksum_url, checksum_file_path)
        # Verify bootstrap iso file's checksum
        if not common.verify_checksum(iso_file_path, checksum_file_path):
            # re-try attempt
            logger.error(
                "Bootstrap ISO checksum mismatch, verification failed")
            return
        logger.debug(
            "Integrity of downloaded bootstrap iso has been successfully verified..")
    except requests.exceptions.RequestException as e:
        logger.error(
            f"failed to download '{get_bootstrap_iso(config)}' file, error: {e}")
        raise
    logger.debug("Download completed for bootstrap ISO file")
    return


def download_bootstrap_checksum(checksum_url, checksum_file_path):
    logger.debug("Downloading bootstrap ISO's checksum file...")

    logger.debug(f"bootstrap iso checksum url: {checksum_url}")
    try:
        response = requests.get(checksum_url, stream=True)
        response.raise_for_status()

        with open(checksum_file_path, "wb") as csum_file:
            for chunk in response.iter_content(chunk_size=8192):
                csum_file.write(chunk)
    except requests.exceptions.RequestException as e:
        logger.error(
            f"failed to download '{checksum_file_path}' file, error: {e}")
        raise
    return


def cleanup_iso_artifacts(iso_path, checksum_path):
    if os.path.exists(iso_path):
        os.remove(iso_path)
    if os.path.exists(checksum_path):
        os.remove(checksum_path)
    logger.debug("ISO artifacts have been deleted successfully")
    return


def remove_iso_file(config, cookies, filename, file_uuid):
    uri = f"/rest/api/web/File/{file_uuid}"
    url = "https://" + get_host_address(config) + uri
    headers = {"x-api-key": get_session_key(
        config), "Content-Type": "application/vnd.ibm.powervm.web+xml;type=File"}
    try:
        response = requests.delete(
            url, headers=headers, cookies=cookies, verify=False)
        if response.status_code != 204:
            logger.error(
                f"failed to remove ISO file '{filename}' from VIOS after uploading to media repository, error: {response.text}")
            raise Exception(
                f"failed to remove ISO file '{filename}' from VIOS after uploading to media repository, error: {response.text}")
    except Exception as e:
        logger.error(
            f"Failed to remove ISO file '{filename}' from VIOS after uploading to media repository, error {e}")

    logger.debug(f"ISO file: '{filename}' removed from VIOS successfully")
    return


def upload_iso_to_media_repository(config, cookies, iso_dir, iso_file_name, sys_uuid, vios_uuid_list):
    # Check if bootstrap ISO file is already uploaded to any of the available VIOS
    if "_pimb" in iso_file_name:
        uploaded, vios_uuid = is_iso_uploaded(
            config, cookies, iso_file_name, sys_uuid, vios_uuid_list)
        if uploaded:
            return vios_uuid

    logger.debug(
        f"Uploading ISO file '{iso_dir}/{iso_file_name} to VIOS media repository")
    # Iterating over the vios_uuid_list to upload the ISO to the media repository for a VIOS
    # If upload operation fails for current VIOS, next available VIOS in the list will be used as a fallback.
    file_uuid = ""
    for index, vios_uuid in enumerate(vios_uuid_list):
        try:
            # Re-run scenario: If lpar is already activated but launch flow failed during monitoring or app_check stage in previous run. Skip reupload of cloudinit iso
            if "_pimc" in iso_file_name:
                exists, _, lpar_uuid = partition.check_partition_exists(
                    config, cookies, sys_uuid)
                if exists:
                    lpar_state = activation.check_lpar_status(
                        config, cookies, lpar_uuid)
                    if lpar_state == "running":
                        logger.debug(
                            f"Partition already in 'running' state, skipping reupload of cloud-init ISO '{iso_file_name}'")
                        return vios_uuid

                    vios = vios_operation.get_vios_details(
                        config, cookies, sys_uuid, vios_uuid)

                    # remove SCSI mapping from VIOS
                    command_util.remove_scsi_mappings(
                        config, cookies, sys_uuid, lpar_uuid, vios_uuid, vios, iso_file_name)

                    # Delete existing cloud-init vOPT with same name if already loaded in VIOS media repository
                    command_util.remove_vopt_device(
                        config, cookies, vios, iso_file_name)

            # Create ISO filepath for bootstrap iso
            iso_file = iso_dir + "/" + iso_file_name
            iso_checksum = common.file_checksum(iso_file)
            iso_size = os.path.getsize(iso_file)
            file_uuid = create_iso_path(
                config, cookies, vios_uuid, iso_file_name, iso_checksum, iso_size)
            # transfer ISO file to VIOS media repository
            with open(iso_file, 'rb') as f:
                uploadfile(config, cookies, f, file_uuid)
                logger.debug(f"'{iso_file_name}' ISO file upload completed!!")

            # remove iso files from VIOS
            remove_iso_file(config, cookies, iso_file, file_uuid)
            return vios_uuid
        except Exception as e:
            logger.error(f"failed to upload ISO to '{vios_uuid}' VIOS")
            if file_uuid != "":
                remove_iso_file(config, cookies, iso_file, file_uuid)
            if index == len(vios_uuid_list)-1:
                raise e
            else:
                logger.debug(
                    "Upload of ISO file will be attempted on next available VIOS")
    return


def create_iso_path(config, cookies, vios_uuid, filename, checksum, filesize):
    uri = "/rest/api/web/File/"
    url = "https://" + get_host_address(config) + uri
    headers = {"x-api-key": get_session_key(
        config), "Content-Type": "application/vnd.ibm.powervm.web+xml;type=File", "Accept": "application/atom+xml"}
    payload = f'''
    <web:File xmlns:web="http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/" schemaVersion="V1_0">
        <web:Filename>{filename}</web:Filename>
        <web:InternetMediaType>application/octet-stream</web:InternetMediaType>
        <web:SHA256>{checksum}</web:SHA256>
        <web:ExpectedFileSizeInBytes>{filesize}</web:ExpectedFileSizeInBytes>
        <web:FileEnumType>BROKERED_MEDIA_ISO</web:FileEnumType>
        <web:TargetVirtualIOServerUUID>{vios_uuid}</web:TargetVirtualIOServerUUID>
    </web:File>
    '''
    response = None
    file_uuid = ""
    try:
        response = requests.put(url, headers=headers,
                                data=payload, cookies=cookies, verify=False)
        if response.status_code != 200:
            logger.error(
                f"failed to create ISO path for file '{filename}', error: {response.text}")
            raise Exception(
                f"failed to create ISO path for file '{filename}', error: {response.text}")
        # extract file uuid from response
        soup = BeautifulSoup(response.text, "xml")
        file_uuid = soup.find("FileUUID").text
    except Exception as e:
        logger.error(f"failed to create ISO path, error: {e}")
        raise e
    logger.debug(f"{filename} ISO path created successfully")

    return file_uuid


def uploadfile(config, cookies, filehandle, file_uuid):
    uri = "/rest/api/web/File/contents/" + file_uuid
    url = "https://" + get_host_address(config) + uri
    headers = {"x-api-key": get_session_key(config), "Content-Type": "application/octet-stream",
               "Accept": "application/vnd.ibm.powervm.web+xml"}

    def readfile(f, chunksize):
        while True:
            d = f.read(chunksize)
            if not d:
                break
            yield d

    try:
        response = requests.put(url, headers=headers, data=readfile(
            filehandle, chunksize=65536), cookies=cookies, verify=False)
        if response.status_code != 204:
            logger.error(
                f"failed to upload ISO file '{filehandle}' to VIOS media repository, error: {response.text}")
            raise Exception(
                f"failed to upload ISO file '{filehandle}' to VIOS media repository, error: {response.text}")
    except Exception as e:
        logger.error(
            f"failed to upload ISO file '{filehandle}' to VIOS media repository, error: {e}")
        raise e
    return


def is_iso_uploaded(config, cookies, iso_file_name,  sys_uuid, vios_uuid_list):
    try:
        for _, vios_uuid in enumerate(vios_uuid_list):
            vios = vios_operation.get_vios_details(
                config, cookies, sys_uuid, vios_uuid)
            _, _, media_repos = get_media_repositories(
                config, cookies, vios)
            vopt_media = media_repos.find_all("VirtualOpticalMedia")
            for vopt in vopt_media:
                if vopt.find(lambda tag: tag.name == "MediaName" and tag.text == iso_file_name):
                    logger.debug(
                        f"Found ISO file '{iso_file_name}' in media repositories")
                    return True, vios_uuid
    except Exception as e:
        raise e
    logger.debug(
        f"ISO file '{iso_file_name}' was not found in the media repositories")
    return False, ""


def get_media_repositories(config, cookies, vios):
    vg_url = ""
    vol_group = None
    media_repos = None
    try:
        # find volume group URL associated with StoragePool
        soup = BeautifulSoup(vios, 'xml')
        storage_pool = soup.find("StoragePools")
        if storage_pool.find("link") is not None:
            vg_url = storage_pool.find("link").attrs['href']
        else:
            logger.error("failed to get volume group hyperlink from VIOS")
            raise Exception("failed to get volume group hyperlink from VIOS")

        # make REST call to volume group URL(vg_url) to get list of media repositories
        headers = {"x-api-key": get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
        response = requests.get(vg_url, headers=headers,
                                cookies=cookies, verify=False)
        if response.status_code != 200:
            logger.error(
                f"failed to get media repositories, error: {response.text}")
            raise Exception(
                f"failed to get media repositories, error: {response.text}")
        soup = BeautifulSoup(response.text, 'xml')
        media_repos = soup.find("MediaRepositories")
        vol_group = soup.find("VolumeGroup")
    except Exception as e:
        logger.error(f"failed to get media repositories, error: {e}")
        raise e
    logger.debug("Obtained media repositories from VIOS successfully")
    return vg_url, vol_group, media_repos
