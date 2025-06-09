import requests
from bs4 import BeautifulSoup

import utils.string_util as util
import utils.common as common
from .storage_exception import StorageError

logger = common.get_logger("storage")

CONTENT_TYPE = "application/vnd.ibm.powervm.uom+xml; Type=VirtualIOServer"

def populate_payload(vios_payload, hmc_host, partition_uuid, system_uuid, physical_volume_name):
    scsi_mapping = f'''
    <VirtualSCSIMapping schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <AssociatedLogicalPartition kb="CUR" kxe="false" href="https://{hmc_host}/rest/api/uom/ManagedSystem/{system_uuid}/LogicalPartition/{partition_uuid}" rel="related"/>
            <Storage kxe="false" kb="CUR">
                <PhysicalVolume schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                    <VolumeName kb="CUR" kxe="false">{physical_volume_name}</VolumeName>
                </PhysicalVolume>
            </Storage>
        </VirtualSCSIMapping>
'''
    phys_bs = BeautifulSoup(scsi_mapping, 'xml')
    vios_bs = BeautifulSoup(vios_payload, 'xml')
    scsi_mappings = vios_bs.find('VirtualSCSIMappings')
    scsi_mappings.append(phys_bs)
    payload = str(vios_bs)
    return payload

def check_if_storage_attached(vios, partition_uuid):
    found = False
    phys_disk = ""
    try:
        soup = BeautifulSoup(vios, 'xml')
        scsi_mappings = soup.find_all('VirtualSCSIMapping')
        # Iterate over all SCSI mappings and look for Storage followed by PhysicalVolume XML tags
        for scsi in scsi_mappings:
            lpar_link = scsi.find("AssociatedLogicalPartition")
            if lpar_link is not None and partition_uuid in lpar_link.attrs["href"]:
                storage = scsi.find("Storage")
                if storage is not None:
                    physical_volume = storage.find("PhysicalVolume")
                    if physical_volume is not None:
                        logger.debug(f"Found storage SCSI mapping for partition '{partition_uuid}' in VIOS")
                        found = True
                        phys_disk = physical_volume.find("VolumeName").text
                        break
    except Exception as e:
        logger.error("failed to check if storage SCSI mapping is present in VIOS")
        raise e
    return found, phys_disk

def check_if_vfc_disk_attached(vios, partition_uuid):
    found = False
    portname = ""
    try:
        soup = BeautifulSoup(vios, 'xml')
        vfc_mappings = soup.find_all('VirtualFibreChannelMapping')
        # Iterate over all SCSI mappings and look for Storage followed by PhysicalVolume XML tags
        for vfc in vfc_mappings:
            lpar_link = vfc.find("AssociatedLogicalPartition")
            if lpar_link is not None and partition_uuid in lpar_link.attrs["href"]:
                port = vfc.find("Port")
                if port is not None:
                    wwpn = port.find("WWPN")
                    logger.debug(f"WWPN for SAN storage: {wwpn}")
                    logger.debug(f"Found VFC storage mapping for partition '{partition_uuid}' in VIOS")
                    found = True
                    portname = port.find("PortName").text
                    break
    except Exception as e:
        logger.error("failed to check if storage SCSI mapping is present in VIOS")
        raise e
    return found, portname

def attach_storage(vios_payload, config, cookies, partition_uuid, system_uuid, vios_uuid, physical_vol_name):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/VirtualIOServer/{vios_uuid}"
    hmc_host = util.get_host_address(config)
    url =  "https://" +  hmc_host + uri
    payload = populate_payload(vios_payload, hmc_host, partition_uuid, system_uuid, physical_vol_name)
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": CONTENT_TYPE}
    response = requests.post(url, headers=headers, cookies=cookies, data=payload, verify=False)

    if response.status_code != 200:
        logger.error(f"failed to attach physical disk to the partition, error: {response.text}")
        raise StorageError(f"failed to attach physical disk to the partition, error: {response.text}")
    return
