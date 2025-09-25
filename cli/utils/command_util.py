import requests

from bs4 import BeautifulSoup

import cli.auth.auth as auth
import cli.storage.storage as storage
import cli.storage.virtual_storage as vstorage
import cli.utils.common as common
import cli.utils.validator as validator
import cli.utils.string_util as util
import cli.utils.iso_util as iso_util
import cli.vios.vios as vios_operation


logger = common.get_logger("command-util")

def initialize_command(config):
    logger.debug("Validate configuration")
    if not validator.validate_config(config):
        return False, "", "", []
    logger.debug("Configuration validated")

    logger.debug("Authenticate with HMC host")
    session_token, cookies = auth.authenticate_hmc(config)
    logger.debug("Authenticated with HMC")

    config["session"] = {"x-api-key": session_token}

    sys_uuid = get_system_uuid(config, cookies)
    logger.debug(f"System UUID: {sys_uuid}")

    if not validator.validate_host_config(config, cookies, sys_uuid):
        return False, "", "", []
    
    if not validator.validate_networks(config, cookies, sys_uuid):
        return False, "", "", []

    vios_uuid_list = vios_operation.get_vios_uuid_list(
        config, cookies, sys_uuid)

    return True, cookies, sys_uuid, vios_uuid_list


def cleanup(config, cookies):
    auth.delete_session(config, cookies)

def remove_vopt_device(config, cookies, vios, vopt_name):
    try:
        vg_url, vol_group, media_repos = iso_util.get_media_repositories(
            config, cookies, vios)
        if media_repos is None:
            logger.error("failed to get media repositories")
            raise Exception("failed to get media repositories")

        found = False
        # remove vopt_name from media repositoy
        vopt_media = media_repos.find_all("VirtualOpticalMedia")
        for v_media in vopt_media:
            if v_media.find("MediaName") is not None and v_media.find("MediaName").text == vopt_name:
                found = True
                v_media.decompose()
                break

        if not found:
            logger.debug(f"vOPT device '{vopt_name}' is not present in media repository")
            return False

        headers = {"x-api-key": util.get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
        # Now update the modified media repositoy list after delete
        response = requests.post(vg_url, data=str(
            vol_group), headers=headers, cookies=cookies, verify=False)
        if response.status_code != 200:
            logger.error(
                f"failed to update volume group after deleting vOPT device from media repository, error: {response.text}")
            return False

        logger.debug(
            f"Virtual optical media '{vopt_name}' has been deleted successfully")
    except Exception as e:
        raise e
    return True


def remove_virtual_disk(config, cookies, vios_uuid, vg_id, vdisk_name):
    try:
        found, vdisk, vg = vstorage.check_if_vdisk_exists(config, cookies, vios_uuid, vg_id, vdisk_name)
        if not found:
            logger.debug(f"No virtualdisk '{vdisk}' is found under volumegroup")
            return
        # drop virtualdisk xml block
        vdisk.decompose()

        uri = f"/rest/api/uom/VirtualIOServer/{vios_uuid}/VolumeGroup/{vg_id}"
        hmc_host = util.get_host_address(config)
        url =  "https://" +  hmc_host + uri
        headers = {"x-api-key": util.get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
        response = requests.post(url, data=str(vg),
            headers=headers, cookies=cookies, verify=False)
        if response.status_code != 200:
            logger.error(
                f"failed to update volume group after deleting virtual disk, error: '{response.text}'")
            return

        logger.debug(
            f"Virtualdisk '{vdisk_name}' has been deleted successfully")
    except Exception as e:
        raise e
    return


def check_if_scsi_mapping_exist(partition_uuid, vios, media_dev_name):
    found = False
    vscsi = None
    soup = None
    try:
        soup = BeautifulSoup(vios, 'xml')
        scsi_mappings = soup.find_all('VirtualSCSIMapping')
        # Iterate over all SCSI mappings and look for Storage followed by PhysicalVolume XML tags
        for scsi in scsi_mappings:
            lpar_link = scsi.find("AssociatedLogicalPartition")
            if lpar_link is not None and partition_uuid in lpar_link.attrs["href"]:
                b_dev = scsi.find("BackingDeviceName")
                if b_dev is not None and b_dev.text == media_dev_name:
                    found = True
                    vscsi = scsi
                    break
    except Exception as e:
        logger.error("failed to check if storage SCSI mapping is present in VIOS")
        raise e
    return found, vscsi, soup


def remove_scsi_mappings(config, cookies, sys_uuid, partition_uuid, vios_uuid, vios, disk_name):
    found, vscsi, vios = check_if_scsi_mapping_exist(partition_uuid, vios, disk_name)
    if not found:
        logger.debug(f"no SCSI mapping available for '{disk_name}' to remove")
        return
    vscsi.decompose()
    updated_vios = str(vios)

    logger.debug(
        f"Payload prepared to remove '{disk_name}' SCSI mappings from VIOS payload")

    uri = f"/rest/api/uom/ManagedSystem/{sys_uuid}/VirtualIOServer/{vios_uuid}"
    hmc_host = util.get_host_address(config)
    url = "https://" + hmc_host + uri
    headers = {
        "x-api-key": util.get_session_key(config), "Content-Type": storage.CONTENT_TYPE}
    response = requests.post(url, headers=headers,
                             cookies=cookies, data=updated_vios, verify=False)

    if response.status_code != 200:
        logger.error(
            f"failed to update VIOS with removed '{disk_name}' mappings, error: {response.text}")
        return

    logger.debug(f"Successfully removed SCSI mappings for '{disk_name}'")
    return


def get_system_uuid(config, cookies):
    uri = "/rest/api/uom/ManagedSystem/quick/All"
    url = "https://" + util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config)}
    response = requests.get(url, headers=headers,
                            cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to get system UUID, error: {response.text}")
        raise Exception(f"failed to get system UUID, error: {response.text}")
    systems = []
    try:
        systems = response.json()
    except requests.JSONDecodeError as e:
        logger.error(
            f"failed to parse json while getting UUID of the system, error: {e}")
        raise

    uuid = ""
    sys_name = util.get_system_name(config)
    for system in systems:
        if system["SystemName"] == sys_name:
            uuid = system["UUID"]
            break

    if "" == uuid:
        logger.error(f"no system available with name '{sys_name}'")
        raise Exception(f"no system available with name '{sys_name}'")

    return uuid
