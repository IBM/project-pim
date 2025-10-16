import requests
import sys

from bs4 import BeautifulSoup

import cli.storage.storage as storage
import cli.storage.virtual_storage as vstorage
import cli.utils.common as common
import cli.utils.command_util as command_util
import cli.utils.string_util as util

from cli.vios.vios_exception import VIOSError

logger = common.get_logger("vios")

def get_vios_details(config, cookies, system_uuid, vios_uuid):
    try:
        uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/VirtualIOServer/{vios_uuid}"
        url = "https://" + util.get_host_address(config) + uri
        headers = {"x-api-key": util.get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=VirtualIOServer"}
        response = requests.get(url, headers=headers,
                                cookies=cookies, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'xml')
        vios = str(soup.find("VirtualIOServer"))
    except requests.exceptions.RequestException as e:
        raise VIOSError(f"failed to get VIOS details for '{vios_uuid}' while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise VIOSError(f"failed to get VIOS details for '{vios_uuid}', error: {e}")
    return vios


def get_vios_uuid_list(config, cookies, system_uuid):
    try:
        uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/VirtualIOServer/quick/All"
        url = "https://" + util.get_host_address(config) + uri
        headers = {"x-api-key": util.get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=VirtualIOServer"}
        response = requests.get(url, headers=headers,
                                cookies=cookies, verify=False)
        response.raise_for_status()

        uuids = []
        sys_name = util.get_system_name(config)
        for vios in response.json():
            if vios["SystemName"] == sys_name:
                uuids.append(vios["UUID"])

        if len(uuids) == 0:
            raise VIOSError(f"no VIOS available for '{sys_name}'")
    except requests.exceptions.RequestException as e:
        raise VIOSError(f"failed to get VIOS list while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise VIOSError(f"failed to get VIOS list, error: {e}")
    return uuids


def get_active_vios(config, cookies, sys_uuid, vios_uuids):
    # active_vios_servers:
    #   KEY   -> vios_uuid
    #   VALUE -> VIOS server details
    # This dictionary helps avoid multiple REST calls to fetch VIOS details.
    active_vios_servers = {}

    for vios_uuid in vios_uuids:
        vios_payload = get_vios_details(config, cookies, sys_uuid, vios_uuid)
        soup = BeautifulSoup(vios_payload, 'xml')
        state = soup.find("ResourceMonitoringControlState")
        if state.text == "active":
            active_vios_servers[vios_uuid] = vios_payload
    return active_vios_servers


def get_vios_with_mediarepo_tag(active_vios_servers):
    vios_uuid_list = []
    for vios_uuid, vios_payload in active_vios_servers.items():
        soup = BeautifulSoup(vios_payload, 'xml')
        media_repos = soup.find("MediaRepositories")
        if media_repos:
            free_memory = calculate_free_space(vios_uuid, media_repos)
            logger.debug(
                f"Media repositories have {free_memory} GB free memory in '{vios_uuid}' VIOS.")
            if free_memory > 3.0:
                vios_uuid_list.append(vios_uuid)
            else:
                logger.error(
                    f"sufficient memory not available in '{vios_uuid}' VIOS for media repositories.")
    return vios_uuid_list


def calculate_free_space(vios_uuid, media_repos):
    used_memory = 0.0
    free_memory = 0.0
    try:
        size_list = media_repos.find_all("Size")
        capacity = float(media_repos.find("RepositorySize").text)
        for size in size_list:
            used_memory += float(size.text)
        free_memory = capacity - used_memory
    except Exception as e:
        logger.error(
            f"failed to calculate free memory in '{vios_uuid}' VIOS for media repositories. error: {e}")
    return free_memory


def get_vios_with_physical_storage(config, active_vios_servers):
    required_capacity = int(util.get_required_disk_size(config)) * 1024
    vios_list = []
    min_volume_capacity = sys.maxsize
    for vios_uuid, vios_payload in active_vios_servers.items():
        soup = BeautifulSoup(vios_payload, 'xml')
        pvs_soup = soup.find("PhysicalVolumes")
        pv_list = pvs_soup.find_all("PhysicalVolume")

        min_volume_capacity = sys.maxsize
        disk_name = ""

        for pv in pv_list:
            available_for_usage = pv.find("AvailableForUsage")
            volume_capacity = int(pv.find("VolumeCapacity").text)
            if available_for_usage.text == "true" and volume_capacity >= required_capacity:
                # Selecting the physical volume with disk capacity nearest to the required storage size
                if volume_capacity < min_volume_capacity:
                    min_volume_capacity = volume_capacity
                    disk_name = pv.find("VolumeName").text
        if disk_name != "":
            vios_list.append((vios_uuid, disk_name, min_volume_capacity))
    vios_list.sort(key=lambda vios: vios[2])
    return vios_list


def get_volume_group(config, cookies, vios_uuid, vg_name):
    try:    
        uri = f"/rest/api/uom/VirtualIOServer/{vios_uuid}/VolumeGroup"
        url = "https://" + util.get_host_address(config) + uri
        headers = {"x-api-key": util.get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
        response = requests.get(url, headers=headers,
                                cookies=cookies, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'xml')
        group = soup.find("GroupName", string=vg_name)
        vol_group = group.parent
        vg_id = vol_group.find("AtomID").text
    except requests.exceptions.RequestException as e:
        raise VIOSError(f"failed to get volume group while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise VIOSError(f"failed to get volume group, error: {e}")
    return vg_id

def cleanup_logical_volume(config, cookies, vios, vios_uuid, sys_uuid, partition_uuid):
    vdisk_found, vdisk = vstorage.check_if_vdisk_attached(vios, partition_uuid)
    if vdisk_found:
        logger.info(
            f"Removing SCSI mapping for virtual disk '{vdisk}'")
        command_util.remove_scsi_mappings(
            config, cookies, sys_uuid, partition_uuid, vios_uuid, vios, vdisk)

    # delete associated virtual disk
    vg_id = get_volume_group(config, cookies, vios_uuid, util.get_volume_group_name(config))
    command_util.remove_virtual_disk(config, cookies, vios_uuid, vg_id, util.get_virtual_disk_name(config))
    logger.info(f"Deleted virtualdisk '{util.get_virtual_disk_name(config)}' associated to partition '{util.get_partition_name(config)}'")
    return

def cleanup_storage(config, cookies, vios, vios_uuid, sys_uuid, partition_uuid):
    storage_cleaned = False
     # remove SCSI mappings from VIOS
    phys_disk_found, phys_disk = storage.check_if_storage_attached(
        vios, partition_uuid)
    if phys_disk_found and not storage_cleaned:
        logger.info(
            f"Removing SCSI mapping for physical disk '{phys_disk}'")
        command_util.remove_scsi_mappings(
            config, cookies, sys_uuid, partition_uuid, vios_uuid, vios, phys_disk)
        storage_cleaned = True
    # Check if attached disk is virtual disk
    if not phys_disk_found and not storage_cleaned and util.use_logical_volume(config):
        cleanup_logical_volume(config, cookies, vios, vios_uuid, sys_uuid, partition_uuid)
        storage_cleaned = True
    return storage_cleaned

def cleanup_vios(config, cookies, sys_uuid, partition_uuid, vios_uuid_list):
    vopt_list = [util.get_bootstrap_iso(
        config), util.get_cloud_init_iso(config)]
    storage_cleaned = False
    processed_vios_list = []
    try:
        for vopt in vopt_list:
            vios_uuid = find_vios_with_vopt_mounted(
                config, cookies, sys_uuid, partition_uuid, vios_uuid_list, vopt)
            if not vios_uuid:
                logger.info(
                    f"no matching VIOS found where {vopt} vOPTs mounted")
                continue
            vios = get_vios_details(config, cookies, sys_uuid, vios_uuid)

            storage_cleaned = cleanup_storage(config, cookies, vios, vios_uuid, sys_uuid, partition_uuid)
            vios = get_vios_details(config, cookies, sys_uuid, vios_uuid)
            logger.info(f"Removing SCSI mapping for vOPT device '{vopt}'")
            command_util.remove_scsi_mappings(
                config, cookies, sys_uuid, partition_uuid, vios_uuid, vios, vopt)

            vios = get_vios_details(config, cookies, sys_uuid, vios_uuid)

            # remove mounted cloud-init vOPT from media repositoy.
            if vopt == util.get_cloud_init_iso(config):
                logger.info(f"Removing vOPT device '{vopt}'")
                command_util.remove_vopt_device(config, cookies, vios, vopt)
            processed_vios_list.append(vios_uuid)

        # If storage and any of the vOPT not using same VIOS, need to cleanup with a different VIOS
        if not storage_cleaned:
            for vios_uuid in vios_uuid_list:
                if vios_uuid not in processed_vios_list:
                    vios = get_vios_details(config, cookies, sys_uuid, vios_uuid)
                    _ = cleanup_storage(config, cookies, vios, vios_uuid, sys_uuid, partition_uuid)
    except Exception as e:
        logger.error(f"failed to clean up VIOS, error: {e}")
        return False
    return True


def find_vios_with_vopt_mounted(config, cookies, sys_uuid, partition_uuid, vios_uuid_list, vopt_name):
    for uuid in vios_uuid_list:
        vios = get_vios_details(config, cookies, sys_uuid, uuid)
        found, _, _ = command_util.check_if_scsi_mapping_exist(partition_uuid, vios, vopt_name)
        if found:
            return uuid
    return ""
