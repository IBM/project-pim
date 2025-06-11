import requests

from bs4 import BeautifulSoup

import auth.auth as auth
import utils.common as common
import utils.validator as validator
import utils.string_util as util
import utils.iso_util as iso_util
import vios.vios as vios_operation
import storage.storage as storage

logger = common.get_logger("action-util")


def initialize_action(config):
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
            logger.debug(
                "vOPT device '{vopt_name}' is not present in media repository")
            return

        headers = {"x-api-key": util.get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
        # Now update the modified media repositoy list after delete
        response = requests.post(vg_url, data=str(
            vol_group), headers=headers, cookies=cookies, verify=False)
        if response.status_code != 200:
            logger.error(
                f"failed to update volume group after deleting vOPT device from media repository, error: {response.text}")
            return

        logger.debug(
            f"Virtual optical media '{vopt_name}' has been deleted successfully")
    except Exception as e:
        raise e
    return


def remove_scsi_mappings(config, cookies, sys_uuid, vios_uuid, vios, disk_name):
    soup = BeautifulSoup(vios, "xml")
    scsi_mappings = soup.find("VirtualSCSIMappings")
    b_devs = scsi_mappings.find_all("BackingDeviceName")
    disk = None
    for b_dev in b_devs:
        if b_dev.text == disk_name:
            disk = b_dev
            break

    if disk is None:
        logger.info(f"no SCSI mapping available for '{disk_name}' to remove")
        return
    scsi1 = disk.parent.parent
    scsi1.decompose()

    logger.debug(
        f"Payload prepared to remove '{disk_name}' SCSI mappings from VIOS payload")

    uri = f"/rest/api/uom/ManagedSystem/{sys_uuid}/VirtualIOServer/{vios_uuid}"
    hmc_host = util.get_host_address(config)
    url = "https://" + hmc_host + uri
    headers = {
        "x-api-key": util.get_session_key(config), "Content-Type": storage.CONTENT_TYPE}
    response = requests.post(url, headers=headers,
                             cookies=cookies, data=str(soup), verify=False)

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
