import requests
from bs4 import BeautifulSoup

import cli.utils.common as common
from cli.storage.storage_exception import StorageError
import cli.utils.string_util as util

logger = common.get_logger("virtual-storage")

def get_vg_payload(physical_vol_name, volume_group):
    return f'''
    <VolumeGroup:VolumeGroup xmlns:VolumeGroup="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2" schemaVersion="V1_0">
        <GroupName kb="CUR" kxe="false">{volume_group}</GroupName>
        <PhysicalVolumes kb="CUD" kxe="false" schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <PhysicalVolume schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <VolumeName kb="CUR" kxe="false">{physical_vol_name}</VolumeName>
            </PhysicalVolume>
        </PhysicalVolumes>
    </VolumeGroup:VolumeGroup>
    '''

def get_vdisk_payload(config, vg_payload):
    vg_soup = BeautifulSoup(vg_payload, 'xml')
    vdisk_payload_str = f'''
    <VirtualDisk schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <DiskCapacity kxe="false" kb="CUR">{util.get_virtual_disk_size(config)}</DiskCapacity>
        <DiskLabel kb="CUR" kxe="false">None</DiskLabel>
        <DiskName kxe="false" kb="CUR">{util.get_virtual_disk_name(config)}</DiskName>
    </VirtualDisk>
    '''
    vdisk_bs = BeautifulSoup(vdisk_payload_str, 'xml')
    vdisks = vg_soup.find("VirtualDisks")
    vdisks.append(vdisk_bs)
    payload = str(vg_soup)
    return payload

def get_vdisk_vios_payload(vios, config, partition_uuid, system_uuid):
    vdisk_mapping = f'''
    <VirtualSCSIMapping schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <AssociatedLogicalPartition kb="CUR" kxe="false" href="https://{util.get_host_address(config)}/rest/api/uom/ManagedSystem/{system_uuid}/LogicalPartition/{partition_uuid}" rel="related"/>
        <Storage kxe="false" kb="CUR">
            <VirtualDisk schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <DiskCapacity kxe="false" kb="CUR">{util.get_virtual_disk_size(config)}</DiskCapacity>
                <DiskLabel kb="CUR" kxe="false">None</DiskLabel>
                <DiskName kxe="false" kb="CUR">{util.get_virtual_disk_name(config)}</DiskName>
            </VirtualDisk>
        </Storage>
    </VirtualSCSIMapping>
    '''
    soup = BeautifulSoup(vios, 'xml')
    vdisk_bs = BeautifulSoup(vdisk_mapping, 'xml')
    scsi_mappings = soup.find('VirtualSCSIMappings')
    scsi_mappings.append(vdisk_bs)
    return str(soup)

def get_volume_group_id(config, cookies, vios_uuid, vg_name):
    uri = f"/rest/api/uom/VirtualIOServer/{vios_uuid}/VolumeGroup"
    hmc_host = util.get_host_address(config)
    url =  "https://" +  hmc_host + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
    try:
        response = requests.get(url, headers=headers, cookies=cookies, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise StorageError(f"failed to get volume group while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise StorageError(f"failed to get volume group, error: {e}")

    soup = BeautifulSoup(response.text, 'xml')
    entries = soup.find_all("entry")
    vg_id = None
    for entry in entries:
        vol_group = entry.find("VolumeGroup")
        if vol_group.find("GroupName").text == vg_name:
            vg_id = entry.find("id").text
    if vg_id is None:
        raise StorageError(f"no matching volumegroup found corresponding to volumegroup name '{vg_name}'")
    return vg_id

def get_volume_group_details(config, cookies, vios_uuid, vg_id):
    uri = f"/rest/api/uom/VirtualIOServer/{vios_uuid}/VolumeGroup/{vg_id}"
    hmc_host = util.get_host_address(config)
    url =  "https://" +  hmc_host + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
    try:
        response = requests.get(url, headers=headers, cookies=cookies, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise StorageError(f"failed to get volume group while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise StorageError(f"failed to get volume group details, error: {e}")
    soup = BeautifulSoup(response.text, 'xml')
    vol_group_details = str(soup.find("VolumeGroup"))
    return vol_group_details

def check_if_vdisk_attached(vios, partition_uuid):
    found = False
    vdisk = ""
    if partition_uuid == "":
        return found, vdisk

    try:
        soup = BeautifulSoup(vios, 'xml')
        scsi_mappings = soup.find_all('VirtualSCSIMapping')
        # Iterate over all SCSI mappings and look for Storage followed by VirtualDisk XML tags
        for scsi in scsi_mappings:
            lpar_link = scsi.find("AssociatedLogicalPartition")
            if lpar_link is not None and partition_uuid in lpar_link.attrs["href"]:
                storage = scsi.find("Storage")
                if storage is not None:
                    logical_vol = storage.find("VirtualDisk")
                    if logical_vol is not None:
                        logger.debug(
                            f"Found virtual disk SCSI mapping for partition '{partition_uuid}' in VIOS")
                        found = True
                        vdisk = logical_vol.find("DiskName").text
                        break
    except Exception as e:
        raise StorageError(f"failed to check if storage SCSI mapping is present in VIOS, error: {e}")
    return found, vdisk

# Checks if virtualdisk is created under a given volumegroup
def check_if_vdisk_exists(config, cookies, vios_uuid, vg_id, vdisk):
    try:
        url = f"https://{util.get_host_address(config)}/rest/api/uom/VirtualIOServer/{vios_uuid}/VolumeGroup/{vg_id}"
        headers = {"x-api-key": util.get_session_key(
            config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
        response = requests.get(url, headers=headers,
                                cookies=cookies, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'xml')

        # remove virtual disk
        volume_group = soup.find("VolumeGroup")
        vdisks = soup.find_all("VirtualDisk")
        present = False
        virt_disk_xml = None
        for disk in vdisks:
            disk_name = disk.find("DiskName")
            if disk_name is not None and disk_name.text == vdisk:
                present = True
                virt_disk_xml = disk
                break
    except requests.exceptions.RequestException as e:
        raise StorageError(f"failed to get volumegroup details while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise StorageError(
                f"failed to get volumegroup details, error: '{e}'")
    return present, virt_disk_xml, volume_group

def create_virtualdisk(config, cookies, vios_uuid, vg_id):
    # Get Volume group details
    vg_details = get_volume_group_details(config, cookies, vios_uuid, vg_id)

    uri = f"/rest/api/uom/VirtualIOServer/{vios_uuid}/VolumeGroup/{vg_id}"
    hmc_host = util.get_host_address(config)
    url =  "https://" +  hmc_host + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; type=VolumeGroup"}
    try:
        payload = get_vdisk_payload(config, vg_details)
        response = requests.post(url, headers=headers, cookies=cookies, data=payload, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise StorageError(f"failed to create virtual disk while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise StorageError(f"failed to create virtual disk, error: {e}")

    logger.info("Successfully created virtual disk")

def attach_virtualdisk(vios_payload, config, cookies, partition_uuid, system_uuid, vios_uuid):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/VirtualIOServer/{vios_uuid}"
    url =  "https://" +  util.get_host_address(config) + uri
    payload = get_vdisk_vios_payload(vios_payload, config, partition_uuid, system_uuid)
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=VirtualIOServer"}
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=payload, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise StorageError(f"failed to attach virtual storage to the partition while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise StorageError(f"failed to attach virtual storage to the partition, error: {e}")
    logger.info("Successfully attached virtual disk")
